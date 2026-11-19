

def languages(repos):

    counts=Counter(); colors={}

    for r in repos:

        lang=(r.get("primaryLanguage") or {}).get("name")

        if lang:

            counts[lang]+=1; colors[lang]=(r.get("primaryLanguage") or {}).get("color") or P["blue"]

    top=counts.most_common(7); total=sum(counts.values())

    s=start_svg(1000,230,"Most used repository languages")

    s+='<text x="30" y="40" class="heading">Languages across public repositories</text>'

    if not top:

        s+='<text x="30" y="95" class="small">No primary language data available yet.</text>'

    else:

        cursor=30

        for lang,count in top:

            portion=count/total; width=max(2,930*portion); color=colors.get(lang,P["blue"])

            s+=f'<rect x="{cursor:.1f}" y="72" width="{width:.1f}" height="16" fill="{esc(color)}"/>'; cursor+=width

        for i,(lang,count) in enumerate(top):

            x=32+(i%4)*240; y=128+(i//4)*42

            s+=f'<circle cx="{x+5}" cy="{y-4}" r="5" fill="{esc(colors.get(lang,P["blue"]))}"/><text x="{x+18}" y="{y}" font-size="14" font-weight="600" fill="{P["text"]}">{esc(lang)}</text><text x="{x+18}" y="{y+17}" class="small">{count/total*100:.1f}% · {count} repos</text>'

    s+='<text x="30" y="213" class="small">Based on primary language of scanned public repositories; not coding time.</text>'

    save("languages.svg",s+end_svg())



def repositories(repos):

    featured=sorted(repos,key=lambda r:(r["stargazerCount"],r["forkCount"]),reverse=True)[:6]

    s=start_svg(1000,100+max(1,len(featured))*65,"Featured public repositories")

    s+='<text x="30" y="40" class="heading">Featured repositories</text>'

    if not featured: s+='<text x="30" y="90" class="small">No public repositories found yet.</text>'

    for i,r in enumerate(featured):

        y=72+i*65; lang=(r.get("primaryLanguage") or {}).get("name") or "—"

        desc=(r.get("description") or "No description provided").replace("\n"," ")

        if len(desc)>86: desc=desc[:83]+"..."

        s+=f'<a href="{esc(r["url"])}"><rect x="26" y="{y-19}" width="948" height="55" rx="10" fill="{P["alt"]}" stroke="{P["border"]}"/><text x="44" y="{y+3}" font-size="16" font-weight="700" fill="{P["blue"]}">{esc(r["name"])}</text><text x="44" y="{y+22}" font-size="12" fill="{P["muted"]}">{esc(desc)}</text><text x="810" y="{y+4}" font-size="12" fill="{P["text"]}">★ {r["stargazerCount"]} · Forks {r["forkCount"]}</text><text x="810" y="{y+22}" font-size="11" fill="{P["muted"]}">{esc(lang)}</text></a>'

    save("repositories.svg",s+end_svg())



def main():

    CARDS.mkdir(exist_ok=True); DATA.mkdir(exist_ok=True)

    user,start,today=fetch_user()

    repos=fetch_repositories()

    cal=user["contributionsCollection"]["contributionCalendar"]

    snapshot={"generated_at":datetime.now(timezone.utc).isoformat(),"username":user["login"],

      "period":{"from":start.isoformat(),"to":today.isoformat()},

      "public_repository_count":user["repositories"]["totalCount"],

      "scanned_repository_count":len(repos),"followers":user["followers"]["totalCount"],

      "following":user["following"]["totalCount"],"total_contributions":cal["totalContributions"],

      "repositories":repos,"contribution_calendar":cal}

    (DATA/"github_stats.json").write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")

    hero(user); stats(user,cal,repos); activity(cal); languages(repos); repositories(repos)

    print(f"Generated cards for @{user['login']}: {cal['totalContributions']} contributions, {len(repos)} repos scanned.")



if __name__=="__main__":

    try: main()

    except Exception as exc:

        print(f"ERROR: {exc}",file=sys.stderr)

        raise
