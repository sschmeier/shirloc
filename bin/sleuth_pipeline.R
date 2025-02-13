# Title     : sleuth_pipeline.R
# Objective : quantify transcript abundance differences between two polysome profiling rna-seq fractions
# Created by: leweezard
# Created on: 9/2/18

# Import sleuth library
library(sleuth)
library(dplyr)

# Read in argument listing all paths of comparisons to perform
args <- commandArgs(trailingOnly = TRUE)
analysis_path <- args[1]
ref_fraction <- args[2]
test_fraction <- args[3]

# Open metadata file stored in paths
s2c <- read.csv(paste(analysis_path,'/sleuth_metadata.txt', sep = ""), sep = ',')
s2c$path <- as.character(s2c$path)

# Filter Function
mod_filter <- function(row, min_reads = 5, min_prop = 0.47) {
  mean(row >= min_reads) >= min_prop
}

# Initialize sleuth object
so <- sleuth_prep(s2c, read_bootstrap = TRUE, extra_bootstrap_summary = TRUE, filter_fun = mod_filter, transformation_function = function(x) log2(x + 0.5))

# Fit LRT 'full' model
so <- sleuth_fit(so, ~fraction, 'full')

# Fit LRT 'reduced' model
so <- sleuth_fit(so, ~1, 'reduced')

# Perform the LRT
so <- sleuth_lrt(so, 'reduced', 'full')

# Perfrom the Wald test
so <- sleuth_wt(so, paste0('fraction'))

# Extract TPM means for fraction and append to table
frac_a <- s2c$sample[s2c$fraction == ref_fraction]
frac_b <- s2c$sample[s2c$fraction == test_fraction]
frac_a_raw <- subset(so$obs_raw,so$obs_raw$sample %in% frac_a)
frac_b_raw <- subset(so$obs_raw,so$obs_raw$sample %in% frac_b)
frac_a_means <- aggregate(tpm~target_id, data = frac_a_raw, FUN=function(x) c(mean=mean(x)))
colnames(frac_a_means) <- c("target_id", paste0("tpm_",ref_fraction))
frac_b_means <- aggregate(tpm~target_id, data = frac_b_raw, FUN=function(x) c(mean=mean(x)))
colnames(frac_b_means) <- c("target_id",paste0("tpm_",test_fraction))
merged_means <- merge(frac_a_means, frac_b_means, by=c("target_id"))


# Generate results table
sleuth_lrt <- sleuth_results(so, 'reduced:full', 'lrt', show_all = TRUE)
sleuth_wt <- sleuth_results(so, 'fraction', show_all = TRUE)
res <- merge(sleuth_lrt, sleuth_wt[, c('target_id', 'b', 'se_b', 'mean_obs')], on = 'target_id', sort = FALSE)
res_wTPM <- left_join(res, merged_means)

# Sort result table
res <- res[order(res[,1]),]

# Extract normalized counts
norm_counts <- kallisto_table(so, normalized = TRUE, include_covariates = TRUE)

# Write results into output file
write.csv(sleuth_lrt, file = paste0(analysis_path,'/sleuth_lrt_output.csv'), quote = FALSE, row.names = FALSE)
write.csv(sleuth_wt, file = paste0(analysis_path,'/sleuth_wt_output.csv'), quote = FALSE, row.names = FALSE)
write.csv(res, file = paste(analysis_path,'/sleuth_output.csv', sep = ""), quote = FALSE, row.names = FALSE)
write.csv(res_wTPM, file = paste(analysis_path,'/sleuth_output_with_tpm.csv', sep = ""), quote = FALSE, row.names = FALSE)
write.csv(norm_counts, file = paste0(analysis_path,'/normalized_counts.csv'), quote = FALSE, row.names = FALSE)