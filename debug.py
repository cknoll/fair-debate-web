import requests
from ipydex import IPS

j0 = {"re_app":"example","re_model":"mytext","re_field_name":"text","re_object_id":"1","re_id":"d993a022-2b67-48c3-857e-0766b99627ef","re_payload":{"type":"Annotation","body":[{"type":"TextualBody","value":"foo21","purpose":"commenting"}],"target":{"selector":[{"type":"TextQuoteSelector","exact":"shipwreck"},{"type":"TextPositionSelector","start":658,"end":667}]},"@context":"http://www.w3.org/ns/anno.jsonld","id":"#d993a022-2b67-48c3-857e-0766b99627ef"}}
j = {"re_app":"example","re_model":"mytext","re_field_name":"text","re_object_id":"",
     "re_id":0,"reviewer_name":"debug_reviewer","re_annotation_list":[
        {"type":"Annotation","body":[{"type":"TextualBody","value":"bar","purpose":"commenting"}],
          "target":{"selector":[{"type":"TextQuoteSelector","exact":"Duis"},{"type":"TextPositionSelector","start":257,"end":261}]},
          "@context":"http://www.w3.org/ns/anno.jsonld","id":"#21b1eb76-17cd-4159-971c-4c2ee824d6d0"},
        {"type":"Annotation","body":[{"type":"TextualBody","value":"foo","purpose":"commenting"}],
         "target":{"selector":[{"type":"TextQuoteSelector","exact":"laborum"},{"type":"TextPositionSelector","start":470,"end":477}]},
         "@context":"http://www.w3.org/ns/anno.jsonld","id":"#84dd4f06-bb04-4da0-a2cb-3acbe7899821"}
    ]
}

response = requests.post('http://localhost:8000/api/add/', json=j)


url2 = "http://localhost:8000/api/get/?re_app=example&re_model=mytext&re_field_name=text&re_object_id=&format=recogito"
url2 = "http://localhost:8000/api/get/?re_app=example&re_model=mytext&re_field_name=text&re_object_id=&_format=recogito"
response = requests.get(url2)

print(response)

IPS()
