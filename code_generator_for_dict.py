l1 = [["a",["1solo","1assist","2"]],["b",["1","2"]],["c",["1solo","1assist","2solo","2assist"]],["d",["1","2"]]]

f = open ("code_dict.txt",'w')

for let in l1:
	f.write(let[0]+'=dict(')
	for num in let[1]:
		f.write('_'+num+"=DeffencesCrossed._run_stats("+let[0]+'_'+num+"_success, "+let[0]+'_'+num+"_failure),")
f.close()
