import pandas as pd, re, sqlite3, json
from pathlib import Path
URL='https://raw.githubusercontent.com/Aashutosh-Shejul/naukri-job-market-analysis/main/staging_raw.csv'
OUT=Path('outputs')
SKILLS=['Python','SQL','Excel','Power BI','Tableau','Machine Learning','Deep Learning','NLP','Pandas','NumPy','Statistics','Java','JavaScript','AWS','Azure','Spark','PySpark','TensorFlow','PyTorch','R','SAS','ETL','Docker','Git','LLM','Data Analysis','Data Visualization','Airflow','Snowflake','Hadoop','Scikit-learn','Generative AI']
def extract(s):
 s=str(s)
 return [k for k in SKILLS if re.search(r'(?<!\w)'+re.escape(k)+r'(?!\w)',s,re.I)]
def clean(raw):
 raw.columns=[re.sub(r'[^a-z0-9]+','_',str(c).lower()).strip('_') for c in raw.columns]
 def col(*names):
  return next((raw[n].fillna('').astype(str) for n in names if n in raw),pd.Series('',index=raw.index))
 d=pd.DataFrame(dict(title=col('job_title','title','jobtitle','designation'),company=col('company','company_name','companyname'),location=col('location','job_location','locations'),experience=col('experience','experience_required','job_experience_required'),salary=col('salary','job_salary'),text=col('skills','key_skills','skill','skills_raw','keyskills','skills_text','skills_required','skill_tags')+' '+col('description','job_description')))
 # Support alternate original headers through semantic matching.
 for field,pattern in [('title','title|designation'),('company','company'),('location','location'),('experience','experience|exp'),('salary','salary'),('text','skill|description')]:
  if not d[field].str.strip().any():
   candidates=[c for c in raw if re.search(pattern,c)]
   if candidates: d[field]=raw[candidates[0]].fillna('').astype(str)
 if not d.title.str.strip().any() or not d.text.str.strip().any(): raise ValueError(f'Cannot identify title/skills: {list(raw.columns)}')
 d=d[d.title.str.strip().ne('')].drop_duplicates().reset_index(drop=True); d.index.name='job_id'; d=d.reset_index()
 d['min_exp']=pd.to_numeric(d.experience.str.extract(r'(\d+)')[0],errors='coerce')
 d['mode']=d.location.str.extract(r'(?i)\b(remote|hybrid|work from home|work from office)\b')[0].str.lower().fillna('Unspecified')
 def salary(s):
  m=re.search(r'(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(?:lacs?|lakhs?|lpa)',s,re.I)
  return (float(m[1])+float(m[2] or m[1]))/2 if m else None
 d['salary_lpa']=d.salary.map(salary)
 d['skills']=d.text.map(extract)
 d['skill_count']=d.skills.str.len()
 return d

def run():
 OUT.mkdir(exist_ok=True)
 raw=pd.read_csv('data.csv' if Path('data.csv').exists() else URL,low_memory=False)
 d=clean(raw); s=d[['job_id','skills']].explode('skills').dropna().rename(columns={'skills':'skill'}); d['skills']=d.skills.map(', '.join)
 d.to_csv(OUT/'jobs.csv',index=False); s.to_csv(OUT/'skills.csv',index=False)
 with sqlite3.connect(OUT/'jobs.sqlite') as con:
  d.to_sql('jobs',con,if_exists='replace',index=False); s.to_sql('skills',con,if_exists='replace',index=False)
  for i,q in enumerate(Path('queries.sql').read_text().split(';'),1):
   if q.strip(): pd.read_sql_query(q,con).to_csv(OUT/f'query_{i:02}.csv',index=False)
 counts=s.skill.value_counts(); cities=d.location.replace('',pd.NA).dropna().value_counts()
 info={'raw_rows':len(raw),'clean_jobs':len(d),'salary_parsed':int(d.salary_lpa.notna().sum()),'skill_coverage':int(d.skill_count.gt(0).sum()),'top_skill':str(counts.index[0]) if len(counts) else 'Unavailable','top_location':str(cities.index[0]) if len(cities) else 'Unavailable'}
 (OUT/'audit.json').write_text(json.dumps(info,indent=2)); print(info)
 (OUT/'findings.md').write_text(f"# Findings\n- {len(d):,} distinct normalized records from {len(raw):,} raw rows.\n- Most frequent recognized skill: {info['top_skill']}. Prioritize this for broad sample coverage, not guaranteed hiring.\n- Most frequent exact location label: {info['top_location']}. Multi-location labels are not individual cities.\n- {info['salary_parsed']:,} salaries parsed in LPA; salary comparisons exclude all other records.\n- Historical sample, not live vacancies; no inferred work modes.")
if __name__=='__main__': run()
