from python_a2a import A2AClient

# Test the servers
llm_client = A2AClient("http://localhost:5011")


llm_result = llm_client.ask("I didn't like the movie which we watched yesterday")

print(llm_result)
