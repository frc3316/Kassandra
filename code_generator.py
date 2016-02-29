l1 = [["a",["1solo","1assist","2"]],["b",["1","2"]],["c",["1solo","1assist","2"]],["d",["1","2"]]]

f = open ("code.txt",'w')

for let in l1:
	for num in let[1]:
		f.write(let[0]+"_"+num+"_success = [match['"+let[0]+"']['"+num+"']['success'] for match in breaching_data]"+'\n')
		f.write(let[0]+"_"+num+"_failure = [match['"+let[0]+"']['"+num+"']['failure'] for match in breaching_data]"'\n')
f.close()

