import sys; sys.path.insert(0, '.')
from data_loader import load_all

dfs = load_all()
be = dfs['bill_extraction']
bill = dfs['bill']
nft = dfs['nft']

print(f"bill_extraction (completed only): {len(be)}")
print(f"bill table total: {len(bill)}")
print(f"NFTs: {len(nft)}")
completed = (bill["status"] == "completed").sum()
print(f"Completed bills in bill table: {completed}")
print(f"Match check: bill_extraction == completed? {len(be) == completed}")
