"""Industrial multilingual query variants are candidates, never evidence."""
TERMS={"gear":{"en":"gear manufacturer","tr":"dişli üreticisi","ru":"производитель шестерен","fa":"تولیدکننده چرخ دنده","ar":"مصنع تروس"},
"shaft":{"en":"industrial shaft manufacturer","tr":"endüstriyel mil üreticisi","ru":"производитель промышленных валов","fa":"تولیدکننده شفت صنعتی","ar":"مصنع أعمدة صناعية"}}
def variants(application,country,product):
 row=TERMS.get(application.lower())
 if not row:return ()
 return tuple({"language":lang,"query":f'{term} {product} {country}',"status":"CANDIDATE"} for lang,term in sorted(row.items()))
