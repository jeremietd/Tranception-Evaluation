# Single sequence metrics
# ESM-1v, ESM-1v-mask6, CARP-640m-logp, Repeat-1, Repeat-2, Repeat-3, Repeat-4

# CARP_640m_logp = True
# ESM_1v = True
# ESM_1v_mask6 = True
# repeat_1 = True
# repeat_2 = True
# repeat_3 = True
# repeat_4 = True

from utils import add_metric
import tempfile
import subprocess
import pandas as pd
from glob import glob
import torch
from pgen.utils import parse_fasta

# target_seqs_file = "/tmp/target_seqs.fasta"
# with open(target_seqs_file,"w") as fh:
#   for target_fasta in glob("/target_seqs/*"):
#     for name, seq in zip(*parse_fasta(target_fasta, return_names=True, clean="unalign")):
#       print(f">{name}\n{seq}", file=fh)

#CARP
def CARP_640m_logp(target_seqs_file, results, device): 
  with tempfile.TemporaryDirectory() as output_dir:
    proc = subprocess.run(['python', "../tmp/extract.py", "carp_640M", target_seqs_file, output_dir + "/", "--repr_layers", "logits", "--include", "logp", "--device", device], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    # print(proc.stderr)
    # print(proc.stdout)
    df = pd.read_table(output_dir + '/carp_640M_logp.tsv')
    df = df.rename(columns={'name': 'id', 'logp': 'carp640m_logp'},)
    for _, row in df.iterrows():
      add_metric(results, row["id"], "CARP-640m", row["carp640m_logp"])

# ESM1v (unmasked)
def ESM_1v(results, device): #TODO: allow other devices?
  if device=='cuda:0':
    torch.cuda.empty_cache()
  for targets_fasta in glob("../target_seqs/*"):
    with tempfile.TemporaryDirectory() as output_dir:
      outfile = output_dir + "/esm_results.tsv"
      proc = subprocess.run(['python', "protein_gibbs_sampler/src/pgen/likelihood_esm.py", "-i", targets_fasta, "-o", outfile, "--model", "esm1v", "--masking_off", "--score_name", "score", "--device", "gpu"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
      # print(proc.stdout)
      # print(proc.stderr)
      df = pd.read_table(outfile)
      for i, row in df.iterrows():
        add_metric(results, row["id"], "ESM-1v", row["score"])
      del df

# ESM1v mask 6
def ESM_1v_mask6(results, device): #TODO: allow other devices?
  if device=='cuda:0':
    torch.cuda.empty_cache()
  for targets_fasta in glob("../target_seqs/*"):
    with tempfile.TemporaryDirectory() as output_dir:
      outfile = output_dir + "/esm_results.tsv"
      proc = subprocess.run(['python', "protein_gibbs_sampler/src/pgen/likelihood_esm.py", "-i", targets_fasta, "-o", outfile, "--model", "esm1v", "--mask_distance", "6", "--score_name", "score", "--device", "gpu"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
      # print(proc.stdout)
      # print(proc.stderr)
      df = pd.read_table(outfile)
      for i, row in df.iterrows():
        add_metric(results, row["id"], "ESM-1v mask6", row["score"])
      del df

# repeat
def find_longest_repeat(seq, k):
  longest = [1] * len(seq)
  pattern = [None] * len(seq)
  
  seq_len = len(seq)
  for i in range(seq_len):
    if i + k <= seq_len:
      pattern[i] = seq[i:i+k]
    if i - k >= 0:
      if pattern[i-k] == pattern[i]:
        longest[i] = longest[i-k] + 1
  return -1 * max(longest)

def Repeat(results):
    repeat_ks = list()
    if repeat_1:
        repeat_ks.append(1)
    if repeat_2:
        repeat_ks.append(2)
    if repeat_3:
        repeat_ks.append(3)
    if repeat_4:
        repeat_ks.append(4)

    for k in repeat_ks:
        for targets_fasta in glob("../target_seqs/*"):
            for name, seq in zip(*parse_fasta(targets_fasta, return_names=True, clean="unalign")):
                score = find_longest_repeat(seq, k)
                add_metric(results, name, f"longest_repeat_{k}", score)