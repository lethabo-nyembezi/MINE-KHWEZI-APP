""app.py - Khwezi Mining Health, Safety and Equipment Monitoring Application (Streamlit).
Run with:  streamlit run app.py"""
import pandas as pd
import plotly.express as px
import streamlit as st
 
import analysis
import auth
import data_loader as dl
import logic as L
 
LOGO = "🚛"  # brand icon shown on the login page, welcome page, sidebar and browser tab
st.set_page_config(page_title="Khwezi Mining Monitor", page_icon=LOGO, layout="wide")
 
DARK, PRIMARY, AMBER, GREEN, RED = "#2A1D14", "#A0522D", "#F5A623", "#2E9E5B", "#D62839"
STATUS_COL = {"Normal": GREEN, "Warning": AMBER, "Critical": RED, "Low": GREEN, "Medium": "#F2C94C", "High": "#E67E22"}
 
 
# ---------- open-pit mine artwork (drawn as SVG so no image files are needed) ----------
def _truck(x, y, s):
    """A simple side-view haul truck. (x, y) is its top-left corner, s is the scale."""
    return (f"<g transform='translate({x},{y}) scale({s})'>"
            "<polygon points='4,30 18,4 84,4 84,30' fill='#F2B705' stroke='#B78900' stroke-width='2'/>"
            "<rect x='86' y='14' width='26' height='22' rx='3' fill='#F2B705' stroke='#B78900' stroke-width='2'/>"
            "<rect x='92' y='18' width='14' height='8' fill='#CFE3EE'/>"
            "<rect x='0' y='30' width='114' height='12' fill='#3A3A3A'/>"
            "<circle cx='28' cy='44' r='16' fill='#1C1C1C'/><circle cx='28' cy='44' r='7' fill='#777'/>"
            "<circle cx='90' cy='44' r='16' fill='#1C1C1C'/><circle cx='90' cy='44' r='7' fill='#777'/>"
            "</g>")
 
 
def _scene_svg():
    """Open pit mine with terraced benches, a haul road and haul trucks. The whole scene is blurred inside the SVG."""
    pit = ("-60,430 240,430 310,500 400,500 470,570 560,570 630,640 730,640 800,710 900,710 970,640 1060,640 "
           "1130,570 1210,570 1280,500 1350,500 1420,430 1660,430 1660,960 -60,960")
    return ("<svg xmlns='http://www.w3.org/2000/svg' width='1600' height='900' viewBox='0 0 1600 900'><defs>"
            "<linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#F3C98B'/><stop offset='1' stop-color='#FBE6C4'/></linearGradient>"
            "<linearGradient id='rock' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#B9814A'/><stop offset='1' stop-color='#5B3A21'/></linearGradient>"
            "<filter id='b' filterUnits='userSpaceOnUse' x='-100' y='-100' width='1800' height='1100'><feGaussianBlur stdDeviation='7'/></filter>"
            "</defs><g filter='url(#b)'>"
            "<rect x='-60' y='-60' width='1720' height='1020' fill='url(#sky)'/>"
            "<circle cx='1230' cy='190' r='80' fill='#FFF4D2'/>"
            "<polygon points='-60,430 -60,350 180,310 400,360 640,290 900,350 1150,300 1400,360 1660,320 1660,430' fill='#C9A079' opacity='.85'/>"
            "<rect x='-60' y='430' width='1720' height='530' fill='#6E4426'/>"
            "<path d='M-60 500H1660M-60 570H1660M-60 640H1660M-60 710H1660' stroke='#8E6039' stroke-width='5' fill='none'/>"
            f"<polygon points='{pit}' fill='url(#rock)'/>"
            "<path d='M-60 430H240M310 500H400M470 570H560M630 640H730M800 710H900M970 640H1060M1130 570H1210M1280 500H1350M1420 430H1660' "
            "stroke='#E3BE88' stroke-width='6' fill='none'/>"
            "<polyline points='1435,430 1300,500 1170,570 1010,640 930,710' stroke='#D8B07A' stroke-width='20' fill='none' "
            "stroke-linecap='round' stroke-linejoin='round' opacity='.85'/>"
            "<ellipse cx='95' cy='425' rx='80' ry='18' fill='#F5DDB5' opacity='.5'/>"
            + _truck(120, 340, 1.5) + _truck(325, 464, .6) + _truck(815, 677, .55) + _truck(1445, 364, 1.1) + _truck(1140, 534, .6) +
            "<ellipse cx='800' cy='690' rx='520' ry='70' fill='#FFE8C2' opacity='.22'/>"
            "</g></svg>")
 
 
def _pit_svg(fill, op):
    """Side view of a terraced open pit with one haul truck - used as a banner and sidebar decoration."""
    return ("<svg xmlns='http://www.w3.org/2000/svg' width='520' height='110' viewBox='0 0 520 110'>"
            f"<polygon points='0,40 60,40 90,58 130,58 160,76 200,76 230,94 300,94 330,76 370,76 400,58 440,58 470,40 520,40 520,110 0,110' fill='{fill}' opacity='{op}'/>"
            "<path d='M0 40H60M90 58H130M160 76H200M230 94H300M330 76H370M400 58H440M470 40H520' stroke='#F5A623' stroke-width='2' fill='none' opacity='.75'/>"
            + _truck(255, 70, .4) + "</svg>")
 
 
def _data_uri(svg):
    return "data:image/svg+xml;utf8," + svg.replace("#", "%23").replace("<", "%3C").replace(">", "%3E")
 
 
PIT_BANNER = _data_uri(_pit_svg("#000", ".28"))
PIT_SIDEBAR = _data_uri(_pit_svg(AMBER, ".16"))
 
# Blurred mine background used on the login page and the welcome page only
SCENE_CSS = ("<style>"
             ".stApp{background-image:linear-gradient(rgba(25,14,6,.38),rgba(25,14,6,.38)),url(\"" + _data_uri(_scene_svg()) + "\");"
             "background-size:cover;background-position:center bottom;background-attachment:fixed;}"
             "[data-testid='stHeader']{background:transparent;}"
             "[data-testid='stForm']{background:rgba(255,255,255,.94);border:none;border-radius:14px;padding:22px 24px;box-shadow:0 8px 28px rgba(0,0,0,.35);}"
             "[data-testid='stForm'] h3,[data-testid='stForm'] [data-testid='stWidgetLabel'] *{color:" + DARK + " !important;}"
             "</style>")
 
st.markdown(f"""<style>
[data-testid="stSidebar"] {{background: url("{PIT_SIDEBAR}") no-repeat bottom / 100% auto, linear-gradient(180deg,{DARK},#4A2E1C);}}
[data-testid="stSidebar"] * {{color:#fff !important;}}
.banner {{background:url("{PIT_BANNER}") no-repeat right bottom / auto 100%, linear-gradient(90deg,{DARK},{PRIMARY});padding:18px 26px;border-radius:12px;color:#fff;margin-bottom:18px;border-left:8px solid {AMBER};}}
.banner h2 {{margin:0;color:#fff;}} .banner p {{margin:2px 0 0;opacity:.85;}}
.card {{background:#fff;border-radius:12px;padding:14px 16px;box-shadow:0 2px 8px rgba(0,0,0,.10);border-top:5px solid var(--c);margin-bottom:12px;}}
.card .v {{font-size:1.9rem;font-weight:700;color:var(--c);}} .card .l {{font-size:.85rem;color:#555;}}
.badge {{display:inline-block;padding:2px 10px;border-radius:12px;color:#fff;font-size:.8rem;font-weight:600;}}
.foot {{text-align:center;color:#777;font-size:.78rem;margin-top:30px;border-top:1px solid #ddd;padding-top:8px;}}
.stButton > button, [data-testid="stFormSubmitButton"] > button, [data-testid="stDownloadButton"] > button {{background:{PRIMARY};border:none;border-radius:8px;font-weight:600;}}
.stButton > button *, [data-testid="stFormSubmitButton"] > button *, [data-testid="stDownloadButton"] > button * {{color:#fff !important;}}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover, [data-testid="stDownloadButton"] > button:hover {{background:{DARK};}}
[data-testid="stSidebar"] .stButton > button {{background:{AMBER};}}
[data-testid="stSidebar"] .stButton > button * {{color:{DARK} !important;font-weight:700;}}
</style>""", unsafe_allow_html=True)
 
 
# ---------- helpers ----------
def banner(title, sub):
    st.markdown(f'<div class="banner"><h2>{title}</h2><p>{sub}</p></div>', unsafe_allow_html=True)
 
 
def cards(items, cols=4):
    palette = [PRIMARY, AMBER, GREEN, RED, "#8E44AD", "#16A5A5"]
    cs = st.columns(cols)
    for i, (label, value) in enumerate(items.items()):
        cs[i % cols].markdown(f'<div class="card" style="--c:{palette[i % len(palette)]}"><div class="v">{value}</div><div class="l">{label}</div></div>', unsafe_allow_html=True)
 
 
def show(df, colour_cols=()):
    """Show a table; colour the cells of status columns."""
    if df.empty:
        st.info("No records match the current selection."); return
    sty = df.style
    for c in colour_cols:
        if c in df.columns:
            f = lambda v: f"background-color:{STATUS_COL.get(str(v).title(), 'white')};color:white;font-weight:600" if str(v).title() in STATUS_COL else ""
            sty = (sty.map if hasattr(sty, "map") else sty.applymap)(f, subset=[c])
    st.dataframe(sty, use_container_width=True, hide_index=True)
 
 
def reload():
    st.session_state["d"] = dl.load_all()
 
 
def allowed(function):
    return auth.has_access(st.session_state["d"]["perms"], st.session_state["user"]["Role"], function)
 
 
# ---------- login ----------
def login_page():
    st.markdown(SCENE_CSS, unsafe_allow_html=True)
    banner(f"{LOGO} Khwezi Mining", "Health, Safety and Equipment Monitoring Application — secure login")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid, st.form("login"):
        st.subheader("Sign in")
        u = st.text_input("Username"); p = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True):
            if not u or not p:
                st.warning("Please enter both username and password.")
            else:
                user = auth.authenticate(st.session_state["d"]["users"], u, p)
                if user is None:
                    st.error("Invalid credentials or inactive account.")
                else:
                    st.session_state["user"] = user; st.session_state["welcomed"] = False; st.rerun()
 
 
# ---------- welcome screen (shown once, straight after login) ----------
def welcome_page(user):
    st.markdown(SCENE_CSS, unsafe_allow_html=True)
    banner(f"{LOGO} Welcome to Khwezi Mining, {user['Full_Name']}", f"{user['Role']} - Health, Safety and Equipment Monitoring Application")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        if st.button("Enter the application", use_container_width=True):
            st.session_state["welcomed"] = True; st.rerun()
        if st.button("Logout", use_container_width=True):
            st.session_state.pop("user"); st.session_state.pop("welcomed", None); st.rerun()
 
 
# ---------- pages ----------
def page_dashboard(d):
    banner("📊 Mining Monitoring Dashboard", "Key performance indicators across safety and equipment")
    cards(L.kpis(d))
    eq, inc = d["equipment"], d["incidents"]
    c1, c2 = st.columns(2)
    m = inc.groupby(inc["Date"].dt.strftime("%Y-%m")).size().reset_index(name="Incidents").rename(columns={"Date": "Month"})
    c1.plotly_chart(px.line(m, x="Month", y="Incidents", markers=True, title="Incident trend by month", color_discrete_sequence=[PRIMARY]), use_container_width=True)
    s = eq["Overall_Status"].value_counts().rename_axis("Status").reset_index(name="Equipment")
    c2.plotly_chart(px.pie(s, names="Status", values="Equipment", hole=.5, title="Equipment status", color="Status", color_discrete_map=STATUS_COL), use_container_width=True)
    c3, c4 = st.columns(2)
    dpt = inc["Department"].value_counts().rename_axis("Department").reset_index(name="Incidents")
    c3.plotly_chart(px.bar(dpt, x="Department", y="Incidents", color="Department", title="Incidents by department", color_discrete_sequence=analysis.COLORS), use_container_width=True)
    rk = L.risk_table(d["risks"])["Classification"].value_counts().rename_axis("Class").reset_index(name="Risks")
    c4.plotly_chart(px.bar(rk, x="Class", y="Risks", color="Class", title="Risk register classification", color_discrete_map=STATUS_COL | {"Critical": RED}), use_container_width=True)
    a = L.all_alerts(eq)
    st.subheader(f"🚨 Latest critical alerts ({(a['Level'] == 'CRITICAL').sum()} active)")
    show(a[a["Level"] == "CRITICAL"].head(8), ["Level"])
 
 
def page_workers(d):
    banner("👷 Worker Health and Safety", "PPE compliance, fatigue, training and risk level")
    w = d["workers"]
    f1, f2, f3 = st.columns(3)
    dep = f1.multiselect("Department", sorted(w["Department"].unique())); sh = f2.multiselect("Shift", sorted(w["Shift"].unique())); rl = f3.multiselect("Risk level", ["Low", "Medium", "High", "Critical"])
    if dep: w = w[w["Department"].isin(dep)]
    if sh: w = w[w["Shift"].isin(sh)]
    if rl: w = w[w["Risk_Level"].isin(rl)]
    cards({"Workers": len(w), "PPE compliant %": round((w["PPE_Compliant"] == "Yes").mean() * 100, 1) if len(w) else 0, "High fatigue (7+)": int((w["Fatigue_Level"] >= 7).sum()), "Training expired": int((w["Safety_Training_Status"] == "Expired").sum())})
    show(w.drop(columns=["Safety_Training_Expiry_Date"]), ["Risk_Level"])
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.pie(w, names="Risk_Level", title="Workers by risk level", color="Risk_Level", color_discrete_map=STATUS_COL), use_container_width=True)
    c2.plotly_chart(px.box(w, x="Department", y="Fatigue_Level", color="Department", title="Fatigue level by department", color_discrete_sequence=analysis.COLORS), use_container_width=True)
    st.subheader("⚠️ Unsafe conditions detected")
    show(L.worker_alerts(w))
 
 
def page_incidents(d):
    banner("🦺 Safety Incident Database", "Add, search, filter and analyse incidents")
    inc = d["incidents"]
    tab1, tab2, tab3 = st.tabs(["View / Search", "Add incident", "Trends"])
    with tab1:
        a, b, c, e = st.columns(4)
        q = a.text_input("Search (ID, cause, type...)"); dep = b.multiselect("Department", sorted(inc["Department"].unique()))
        sev = c.multiselect("Severity", ["Low", "Medium", "High", "Critical"]); stt = e.multiselect("Status", sorted(inc["Incident_Status"].unique()))
        r = inc.copy()
        if q: r = r[r.astype(str).apply(lambda s: s.str.contains(q, case=False)).any(axis=1)]
        if dep: r = r[r["Department"].isin(dep)]
        if sev: r = r[r["Severity"].isin(sev)]
        if stt: r = r[r["Incident_Status"].isin(stt)]
        cards({"Incidents shown": len(r), "Lost-time injuries": int((r["Lost_Time_Injury"] == "Yes").sum()), "High/Critical": int(r["Severity"].isin(["High", "Critical"]).sum()), "Not closed": int((r["Incident_Status"] != "Closed").sum())})
        show(r.assign(Date=r["Date"].dt.strftime("%Y-%m-%d")), ["Severity"])
    with tab2:
        with st.form("add_inc", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            dt = c1.date_input("Date"); tm = c2.time_input("Time"); wid = c3.selectbox("Worker ID", d["workers"]["Worker_ID"])
            loc = c1.selectbox("Location", sorted(inc["Location"].unique())); dep = c2.selectbox("Department", sorted(inc["Department"].unique())); typ = c3.selectbox("Incident type", sorted(inc["Incident_Type"].unique()))
            sev = c1.selectbox("Severity", ["Low", "Medium", "High", "Critical"]); injury = c2.selectbox("Injury status", sorted(inc["Injury_Status"].unique())); days = c3.number_input("Lost days", 0, 365, 0)
            cause = c1.selectbox("Cause", sorted(inc["Cause"].unique())); eqid = c2.selectbox("Equipment ID (optional)", [""] + sorted(d["equipment"]["Equipment_ID"])); stt = c3.selectbox("Status", ["Open", "Under Investigation", "Closed"])
            action = st.text_input("Corrective action")
            if st.form_submit_button("Save incident"):
                if not action.strip(): st.error("Corrective action is required.")
                elif injury == "Lost Time Injury" and days == 0: st.error("A lost-time injury must have at least 1 lost day.")
                elif injury != "Lost Time Injury" and days > 0: st.error("Lost days only apply to lost-time injuries.")
                else:
                    shift = "Day" if 6 <= tm.hour < 18 else "Night"
                    new = {"Incident_ID": f"INC-2026-{len(inc) + 1:04d}", "Date": pd.Timestamp(dt), "Time": tm.strftime("%H:%M"), "Shift": shift, "Location": loc, "Department": dep, "Incident_Type": typ, "Severity": sev, "Injury_Status": injury, "Lost_Time_Injury": "Yes" if injury == "Lost Time Injury" else "No", "Lost_Days": int(days), "Cause": cause, "Corrective_Action": action, "Incident_Status": stt, "Worker_ID": wid, "Equipment_ID": eqid or None}
                    out = pd.concat([inc, pd.DataFrame([new])], ignore_index=True)
                    dl.save_csv(out, "safety_incidents.csv"); reload()
                    st.success(f"Incident {new['Incident_ID']} saved."); st.rerun()
    with tab3:
        m = inc.groupby([inc["Date"].dt.strftime("%Y-%m"), "Severity"]).size().reset_index(name="Incidents").rename(columns={"Date": "Month"})
        st.plotly_chart(px.bar(m, x="Month", y="Incidents", color="Severity", title="Monthly incidents by severity", color_discrete_map={"Low": GREEN, "Medium": "#F2C94C", "High": "#E67E22", "Critical": RED}), use_container_width=True)
        t = inc["Incident_Type"].value_counts().reset_index(); t.columns = ["Incident_Type", "Count"]
        st.plotly_chart(px.bar(t, x="Count", y="Incident_Type", orientation="h", title="Incidents by type", color="Count", color_continuous_scale="Oranges"), use_container_width=True)
 
 
def live_equipment(eq):
    """Recalculate condition from temperature and vibration using the logic module."""
    e = eq.copy()
    e["Temp status"] = e["Temperature_C"].map(L.classify_temperature); e["Vib status"] = e["Vibration_mm_s"].map(L.classify_vibration)
    e["Message"] = [L.equipment_message(t, v) for t, v in zip(e["Temperature_C"], e["Vibration_mm_s"])]
    return e
 
 
def page_equipment(d):
    banner("🚜 Equipment Condition Monitoring", "Temperature and vibration against prototype thresholds")
    e = live_equipment(d["equipment"])
    a, b = st.columns(2)
    typ = a.multiselect("Equipment type", sorted(e["Equipment_Type"].unique())); stt = b.multiselect("Overall status", ["Normal", "Warning", "Critical"])
    if typ: e = e[e["Equipment_Type"].isin(typ)]
    if stt: e = e[e["Overall_Status"].isin(stt)]
    cards({"Equipment shown": len(e), "Critical": int((e["Overall_Status"] == "Critical").sum()), "Warning": int((e["Overall_Status"] == "Warning").sum()), "Avg availability %": round(e["Availability_Percent"].mean(), 1) if len(e) else 0})
    show(e[["Equipment_ID", "Equipment_Type", "Manufacturer", "Operating_Hours", "Temperature_C", "Temp status", "Vibration_mm_s", "Vib status", "Availability_Percent", "Overall_Status"]], ["Temp status", "Vib status", "Overall_Status"])
    st.subheader("Trend for one machine")
    eid = st.selectbox("Equipment ID", sorted(d["equipment"]["Equipment_ID"]))
    r = d["readings"].query("Equipment_ID == @eid"); row = d["equipment"].query("Equipment_ID == @eid").iloc[0]
    st.info(L.equipment_message(row["Temperature_C"], row["Vibration_mm_s"]))
    c1, c2 = st.columns(2)
    f1 = px.line(r, x="Date", y="Temperature_C", title="Temperature (C)", markers=True, color_discrete_sequence=[RED]); f1.add_hline(y=L.TEMP_WARN, line_dash="dash", line_color=AMBER); f1.add_hline(y=L.TEMP_CRIT, line_dash="dash", line_color=RED)
    f2 = px.line(r, x="Date", y="Vibration_mm_s", title="Vibration (mm/s)", markers=True, color_discrete_sequence=[PRIMARY]); f2.add_hline(y=L.VIB_WARN, line_dash="dash", line_color=AMBER); f2.add_hline(y=L.VIB_CRIT, line_dash="dash", line_color=RED)
    c1.plotly_chart(f1, use_container_width=True); c2.plotly_chart(f2, use_container_width=True)
    st.caption("Dashed lines: warning (amber) and critical (red) prototype thresholds.")
 
 
def page_maintenance(d):
    banner("🔧 Equipment Maintenance Monitoring", "Availability = Operating / (Operating + Downtime) x 100")
    e = d["equipment"].copy(); e["Availability (calc) %"] = [L.calculate_availability(o, dn) for o, dn in zip(e["Period_Operating_Hours"], e["Downtime_Hours"])]
    cards({"Due soon (14 days)": int(e["Due_Soon"].sum()), "Overdue": int(e["Overdue"].sum()), "Under maintenance": int(e["Under_Maintenance"].sum()), "Excessive downtime": int(e["Excessive_Downtime"].sum()), "Repeated alerts": int(e["Repeated_Alerts"].sum()), "Low availability": int(e["Low_Availability"].sum())}, 3)
    cols = ["Equipment_ID", "Equipment_Type", "Department", "Next_Maintenance_Date", "Days_To_Next_Maintenance", "Availability (calc) %", "Downtime_Hours", "Priority_Tier"]
    t = st.tabs(["Due soon", "Overdue", "Under maintenance", "Excessive downtime", "Repeated alerts", "Low availability"])
    for tab, flt in zip(t, ["Due_Soon", "Overdue", "Under_Maintenance", "Excessive_Downtime", "Repeated_Alerts", "Low_Availability"]):
        with tab: show(e[e[flt]][cols].assign(Next_Maintenance_Date=lambda x: x["Next_Maintenance_Date"].dt.strftime("%Y-%m-%d")))
    g = e.groupby("Equipment_Type")["Availability (calc) %"].mean().round(1).reset_index()
    st.plotly_chart(px.bar(g, x="Equipment_Type", y="Availability (calc) %", color="Equipment_Type", title="Average availability by equipment type", color_discrete_sequence=analysis.COLORS, text_auto=True), use_container_width=True)
 
 
def page_risk(d):
    banner("⚖️ Risk Assessment", "Risk Score = Likelihood x Consequence (1-5 scale)")
    rt = L.risk_table(d["risks"])
    for _, r in rt[rt["Classification"].isin(["High", "Critical"])].head(5).iterrows():
        (st.error if r["Classification"] == "Critical" else st.warning)(f"{r['Risk_ID']} - {r['Hazard_Category']} ({r['Department']}): {L.risk_warning(r['Risk_Score'])}")
    show(rt.drop(columns=["Risk_Description"]).assign(Next_Review_Date=rt["Next_Review_Date"].dt.strftime("%Y-%m-%d")), ["Classification"])
    st.subheader("Risk calculator")
    a, b = st.columns(2); lk = a.slider("Likelihood", 1, 5, 3); cq = b.slider("Consequence", 1, 5, 3)
    sc = L.risk_score(lk, cq); cl = L.risk_class(sc)
    st.markdown(f'Score **{sc}** → <span class="badge" style="background:{STATUS_COL.get(cl, RED)}">{cl}</span>', unsafe_allow_html=True)
    if L.risk_warning(sc): st.error(L.risk_warning(sc))
    mat = pd.DataFrame([[l * c for c in range(1, 6)] for l in range(5, 0, -1)], index=[f"L{l}" for l in range(5, 0, -1)], columns=[f"C{c}" for c in range(1, 6)])
    st.plotly_chart(px.imshow(mat, text_auto=True, color_continuous_scale=["#2E9E5B", "#F2C94C", "#E67E22", "#D62839"], title="Risk matrix"), use_container_width=True)
 
 
def page_alerts(d):
    banner("🚨 Alerts and Notifications", "Generated automatically from the predefined conditions")
    if allowed("Equipment data"):
        a = L.all_alerts(d["equipment"]); lvl = st.radio("Level", ["All", "CRITICAL", "WARNING"], horizontal=True)
        if lvl != "All": a = a[a["Level"] == lvl]
        show(a, ["Level"])
        if len(a):
            st.markdown("**Alert preview (Figure 1 format)**"); st.code(L.format_alert(a.iloc[st.number_input("Alert number", 1, len(a), 1) - 1]), language="text")
    if allowed("Worker safety data"):
        st.subheader("Worker safety warnings"); show(L.worker_alerts(d["workers"]))
 
 
def page_analysis(d):
    banner("🔍 Interactive Data Analysis", "Answer mining engineering questions from the data")
    inc = d["incidents"]; lo, hi = inc["Date"].min().date(), inc["Date"].max().date()
    rng = st.date_input("Incident period", (lo, hi), min_value=lo, max_value=hi)
    if len(rng) == 2: inc = inc[(inc["Date"] >= pd.Timestamp(rng[0])) & (inc["Date"] <= pd.Timestamp(rng[1]))]
    ok = {q: v for q, v in analysis.QUESTIONS.items() if v[0] == "both" and allowed("Equipment data") and allowed("Worker safety data") or v[0] == "equipment" and allowed("Equipment data") or v[0] == "safety" and allowed("Safety incidents")}
    q = st.selectbox("Choose a question", list(ok))
    table, fig, text = ok[q][1](d, inc)
    st.success(text)
    if fig is not None: st.plotly_chart(fig, use_container_width=True)
    show(table)
 
 
def page_reports(d):
    banner("📄 Reports", "Download data and summaries as CSV")
    inc = d["incidents"]
    if allowed("Safety incidents"):
        st.download_button("⬇ Incident summary (by department & severity)", inc.groupby(["Department", "Severity"]).size().reset_index(name="Incidents").to_csv(index=False), "incident_summary.csv")
    if allowed("Equipment data"):
        st.download_button("⬇ Equipment alerts", L.all_alerts(d["equipment"]).to_csv(index=False), "equipment_alerts.csv")
        st.download_button("⬇ Maintenance priority list", d["equipment"].sort_values("Priority_Score", ascending=False)[["Equipment_ID", "Equipment_Type", "Maintenance_Status", "Priority_Score", "Priority_Tier", "Recommended_Action"]].to_csv(index=False), "maintenance_priority.csv")
    if allowed("Risk assessment"):
        st.download_button("⬇ Risk register with scores", L.risk_table(d["risks"]).to_csv(index=False), "risk_register_scored.csv")
    if allowed("Worker safety data"):
        st.download_button("⬇ Worker safety warnings", L.worker_alerts(d["workers"]).to_csv(index=False), "worker_warnings.csv")
    st.subheader("Management recommendations")
    k = L.kpis(d); recs = [f"Inspect the **{k['Critical equipment']}** critical machines immediately.", f"Schedule the **{k['Overdue maintenance']}** overdue maintenance jobs.", f"Raise PPE compliance (currently **{k['PPE compliance %']}%**).", f"Close the **{k['Open incidents']}** open or under-investigation incidents."]
    for r in recs: st.markdown(f"- {r}")
 
 
def page_users(d):
    banner("👥 Manage Users", "Administrator only")
    u = d["users"]; show(u.drop(columns=["Salt", "Password_Hash"]))
    with st.form("new_user", clear_on_submit=True):
        c1, c2, c3 = st.columns(3); un = c1.text_input("Username"); nm = c2.text_input("Full name"); pw = c3.text_input("Password", type="password")
        role = c1.selectbox("Role", ["Administrator", "Safety Officer", "Mining Engineer", "Maintenance Engineer", "Manager"]); dp = c2.text_input("Department"); em = c3.text_input("Email")
        if st.form_submit_button("Add user"):
            if not (un and nm and pw and em): st.error("All fields are required.")
            elif len(pw) < 8: st.error("Password must be at least 8 characters.")
            elif un.lower() in u["Username"].str.lower().values: st.error("Username already exists.")
            else:
                s = auth.new_salt()
                row = {"User_ID": f"U{len(u) + 1:03d}", "Username": un, "Full_Name": nm, "Role": role, "Department": dp, "Email": em, "Salt": s, "Password_Hash": auth.hash_password(pw, s), "Active": "Yes"}
                dl.save_csv(pd.concat([u, pd.DataFrame([row])], ignore_index=True), "users.csv"); reload(); st.success("User added."); st.rerun()
    c1, c2 = st.columns(2); who = c1.selectbox("Activate / deactivate", u["Username"]); act = c2.radio("Set account", ["Yes", "No"], horizontal=True)
    if st.button("Update account"):
        if who == st.session_state["user"]["Username"]: st.error("You cannot change your own account.")
        else:
            u.loc[u["Username"] == who, "Active"] = act; dl.save_csv(u, "users.csv"); reload(); st.success("Updated."); st.rerun()
 
 
# ---------- main ----------
PAGES = {"📊 Dashboard": ("View dashboard", page_dashboard), "👷 Worker Safety": ("Worker safety data", page_workers), "🦺 Safety Incidents": ("Safety incidents", page_incidents),
         "🚜 Equipment": ("Equipment data", page_equipment), "🔧 Maintenance": ("Maintenance data", page_maintenance), "⚖️ Risk Assessment": ("Risk assessment", page_risk),
         "🚨 Alerts": ("View dashboard", page_alerts), "🔍 Data Analysis": ("View dashboard", page_analysis), "📄 Reports": ("Generate reports", page_reports), "👥 Manage Users": ("Manage users", page_users)}
 
 
def main():
    if "d" not in st.session_state: reload()
    if "user" not in st.session_state: login_page(); return
    user, d = st.session_state["user"], st.session_state["d"]
    if not st.session_state.get("welcomed"): welcome_page(user); return
    menu = [p for p, (fn, _) in PAGES.items() if auth.has_access(d["perms"], user["Role"], fn)]
    with st.sidebar:
        st.markdown(f"## {LOGO} Khwezi Mining")
        st.markdown(f"Welcome,  \n**{user['Full_Name']}**  \n{user['Role']}")
        page = st.radio("Navigation", menu, label_visibility="collapsed")
        if st.button("Logout", use_container_width=True): st.session_state.pop("user"); st.session_state.pop("welcomed", None); st.rerun()
    try:
        PAGES[page][1](d)
    except Exception as ex:  # error prevention: show a message instead of crashing the app
        st.error(f"Something went wrong on this page: {ex}")
    st.markdown('<div class="foot">Educational prototype - thresholds are not real manufacturer or mine safety limits. MINN2020A, University of the Witwatersrand.</div>', unsafe_allow_html=True)
 
 
main()
 
