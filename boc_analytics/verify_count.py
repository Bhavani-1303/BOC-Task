import sys; sys.path.insert(0, '.')
from data_loader import load_all
dfs = load_all()
be = dfs["bill_extraction"]
bill = dfs["bill"]
nft = dfs["nft"]
print(f"bill_extraction count (after filter): {len(be)}")
print(f"bill count: {len(bill)}")
print(f"nft count: {len(nft)}")
print(f"completed bills in bill table: {len(bill[bill['status']=='completed'])}")
