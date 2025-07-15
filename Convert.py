import json, Convert

for file in ["inventory-service/openapi_inventory.json", "mcp-server/openapi_mcp.json"]:
    with open(file) as f: data = json.load(f)
    with open(file.replace(".json", ".yaml"), "w") as f: Convert.dump(data, f, sort_keys=False)
