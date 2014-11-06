from lxml import html
import requests
import json

page = requests.get('http://www.urbandictionary.com/yesterday.php')
tree = html.fromstring(page.text)

terms = tree.xpath('//div[@id="columnist"]//li/a/text()')

print 'Terms: ', terms

with open('terms.txt', 'w') as outfile:
  json.dump(terms, outfile)