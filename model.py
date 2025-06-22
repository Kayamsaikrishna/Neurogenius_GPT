from huggingface_hub import snapshot_download

# Specify the model repository and local directory
repo_id = "deepseek-ai/deepseek-vl2-small"
local_dir = "c:/Users/kayam_drhfn9o/neurogenius/NeuroGenius_App/models/deepseek-vl2-small"

# Download the repository snapshot
snapshot_download(repo_id, local_dir=local_dir, resume_download=True)

print(f"Model files downloaded to: {local_dir}")