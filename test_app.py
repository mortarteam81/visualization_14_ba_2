import pandas as pd
import plotly.express as px

df = pd.read_csv(
    r'd:\20_AI_Workspace\10_Projects\10_visualization_\14-ba-2.-beobjeongbudamgeum-budam-hyeonhwang_daehag_beobjeongbudamgeum-budamryul-20260309-seoul-sojae-saribdaehag.csv',
    encoding='cp949'
)
df = df[['기준년도', '학교명', '부담율']].copy()
df['부담율'] = pd.to_numeric(df['부담율'], errors='coerce')
df = df.dropna(subset=['부담율'])
df['기준년도'] = df['기준년도'].astype(int)
print("Data OK:", df.shape)
print("Columns:", df.columns.tolist())
print("Years:", sorted(df['기준년도'].unique()))
print("Schools count:", df['학교명'].nunique())

# plotly 테스트
filtered_df = df[df['학교명'].isin(df['학교명'].unique()[:5])]
fig = px.line(filtered_df, x='기준년도', y='부담율', color='학교명', markers=True)
try:
    fig.add_hline(y=10, line_dash="dash", line_color="red",
                  annotation_text="10% 기준선", annotation_position="top right")
    print("add_hline with annotation_position: OK")
except Exception as e:
    print("add_hline ERROR:", e)

# pivot 테스트
try:
    pivot = filtered_df.pivot(index='기준년도', columns='학교명', values='부담율')
    print("pivot OK:", pivot.shape)
except Exception as e:
    print("pivot ERROR:", e)
