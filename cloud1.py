from pytagcloud import create_tag_image, make_tags
from pytagcloud.lang.counter import get_tag_counts
import sys
from collections import Counter

if __name__ == '__main__':
    # if len(sys.argv) != 3:
    #     print('usage: %s <doc1> <doc2>')
    #     sys.exit(1)
    # else:
	words1 = Counter()
	words2 = Counter()
	file1 = "Mr. Cuomo, who in 2011 described a new high tax bracket as a short-term solution to help the state weather a financial emergency, did not mention his desire to extend the new tax bracket when he publicly announced his budget proposal in January, or in the weeks since as he and his cabinet members have crisscrossed the state, promoting his spending plan to residents."
	file2 = "The Legislature Legislature Legislature Legislature Legislature Legislature has not held any hearings or debate about the tax proposal, and Mr. Cuomos office has declined to provide details while it is being negotiated. The State Democratic Party has even broadcast television advertisements praising the lack of any tax increases in the spending plan that Mr. Cuomo proposed."	
	file1 = file1.split()
	file2= file2.split()
	# file1 = readFile(sys.argv[1])
	# file2 = readFile(sys.argv[2])
	for w in file1:
		w = w.lower()
		for e in w:
			w = ''.join(e for e in w if (e.isalnum() or e == "'"))
		words1[w] += 1
	for w in file2:
		w = w.lower()
		for e in w:
			w = ''.join(e for e in w if (e.isalnum() or e == "'"))
		words2[w] += 1
	text = {}
	for word in words1:
		if word in words2:
			difference  = words1[word] - words2[word]
			text[word] = difference
		else:
			count = words1[word]
			text[word] = count
	for word in words2:
		if word not in words1:
			count = words2[word]
			text[word] = count*(-1)

	string1 = ""
	string2 = ""
	for w in text:
		if text[w] > 0:
			for j in range(0, text[w]):
				string1 += (w + " ")
		else:
			for j in range(text[w], 0):
				string2 += (w + " ")
	#still need to work out kinks in terms of negative number for second text
	tags1 = make_tags(get_tag_counts(string1), maxsize=40)
	tags2 = make_tags(get_tag_counts(string2), maxsize=40)
	create_tag_image(tags1, 'cloud_large1.png', size=(900, 600), fontname='Droid Sans')
	create_tag_image(tags2, 'cloud_large2.png', size=(900, 600), fontname='Droid Sans')

	import webbrowser
	webbrowser.open('cloud_large1.png') # see results
	webbrowser.open('cloud_large2.png') # see results