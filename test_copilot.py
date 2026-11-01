from copilot import ask

r = ask('What is the total revenue?')
print(r['sql'])
print(r['df'])
print(r['summary'])