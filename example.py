from data import Retrieve

case_retriever = Retrieve.get_case_retriever()
criteria_retriever = Retrieve.get_criteria_retriever()
query = "LNG 트럭용에 관한 RFP를 작성하려고 하는데 관련 사례를 찾아줘."

print(case_retriever.invoke(query))
print(criteria_retriever.invoke(query))

results = Retrieve.double_retrieve(query)

print(results)
