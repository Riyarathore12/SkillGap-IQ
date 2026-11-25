import streamlit as st,pandas as pd,plotly.express as px,json
from pathlib import Path
st.set_page_config(page_title='SkillGap IQ',page_icon='📊',layout='wide')
st.markdown('''<style>.stApp{background:#0b1424;color:#e2e8f0}[data-testid="stMetric"]{background:#18283d;padding:18px;border-radius:14px;border:1px solid #334155}h1,h2,h3{color:#5eead4!important}</style>''',unsafe_allow_html=True)
st.title('SkillGap IQ | Day 11 · Talent Intelligence')
st.caption('Historical Indian data-job postings • observed sample, not live vacancies')
d=pd.read_csv('outputs/jobs.csv').fillna({'skills':'','location':'','company':''}); s=pd.read_csv('outputs/skills.csv')
options=sorted(d.title.unique()); roles=st.sidebar.multiselect('Job titles',options); fresh=st.sidebar.checkbox('Minimum experience ≤ 2 years'); mode=st.sidebar.multiselect('Work mode',sorted(d['mode'].unique()))
if roles:d=d[d.title.isin(roles)]
if fresh:d=d[d.min_exp.le(2)]
if mode:d=d[d['mode'].isin(mode)]
s=s[s.job_id.isin(d.job_id)]; counts=s.skill.value_counts().rename_axis('skill').reset_index(name='postings')
for c,(label,value) in zip(st.columns(4),[('Postings',f'{len(d):,}'),('Recognized skills',len(counts)),('Parsed salaries',int(d.salary_lpa.notna().sum())),('Median disclosed LPA',f'{d.salary_lpa.median():.1f}' if d.salary_lpa.notna().any() else 'N/A')]):c.metric(label,value)
a,b,c,e=st.tabs(['Market overview','Skill gap','SQL lab','Findings'])
def chart(frame,x,y,title):
 st.plotly_chart(px.bar(frame,x=x,y=y,title=title,template='plotly_dark',color_discrete_sequence=['#2dd4bf']),use_container_width=True)
with a:
 l,r=st.columns(2)
 with l:chart(counts.head(15),'skill','postings','Top recognized skills')
 with r:chart(d.title.value_counts().head(10).rename_axis('title').reset_index(name='postings'),'title','postings','Top job titles')
 l,r=st.columns(2)
 with l:chart(d.location.replace('',pd.NA).value_counts().head(10).rename_axis('location').reset_index(name='postings'),'location','postings','Top exact location labels')
 with r:chart(d['mode'].value_counts().rename_axis('mode').reset_index(name='postings'),'mode','postings','Explicit work modes')
 if d.salary_lpa.notna().any():st.plotly_chart(px.histogram(d.dropna(subset=['salary_lpa']),x='salary_lpa',title='Disclosed salary distribution (LPA)',template='plotly_dark'))
with b:
 have=st.multiselect('Your skills',sorted(s.skill.unique())); missing=counts[~counts.skill.isin(have)]
 chart(missing.head(12),'skill','postings','Learning priorities by demand')
 if have:
  from sklearn.feature_extraction.text import TfidfVectorizer
  from sklearn.metrics.pairwise import cosine_similarity
  if len(d):
   # Treat each extracted skill as a single token, including multiword skills.
   corpus=[z.split(', ') for z in d.skills]+[have]; v=TfidfVectorizer(analyzer=lambda z:z,lowercase=False); m=v.fit_transform(corpus); scores=cosine_similarity(m[-1],m[:-1]).ravel(); ranked=d.assign(similarity=scores); st.dataframe(ranked[ranked.similarity>0].nlargest(20,'similarity')[['title','company','location','skills','similarity']],hide_index=True)
 st.caption('Similarity is skill overlap, not hiring probability or eligibility.')
with c:
 st.caption('SQL outputs cover the full dataset, independent of sidebar filters.')
 p=st.selectbox('Select query',sorted(Path('outputs').glob('query_*.csv')),format_func=lambda x:x.stem); st.dataframe(pd.read_csv(p));st.download_button('Export SQL result',p.read_bytes(),p.name)
with e:st.markdown(Path('outputs/findings.md').read_text());st.json(json.loads(Path('outputs/audit.json').read_text()))
st.download_button('Download filtered data',d.to_csv(index=False),'filtered_jobs.csv')
