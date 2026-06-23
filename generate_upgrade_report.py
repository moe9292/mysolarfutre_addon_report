#!/usr/bin/env python3
"""
mySolarFuture - Erweiterungs-Empfehlung 4 -> 8 Module (Upgrade-Bericht)
Vorher/Nachher fuer Bestandskunden mit SolarFlow 800 Pro.
Topologie: 4 Mod DC + 4 Mod via 2. 800W-WR am AC-Eingang. Bleibt 800W Steckersolar.
Preis als Variable.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from generate_report_v5 import (C_PRIMARY, C_ACCENT, C_ACCENT_DARK, C_BLUE, C_DARK,
    C_GRAY, C_LIGHT, C_WHITE, C_RED, C_BG_LIGHT, C_BG_ACCENT, W, H,
    draw_header, draw_footer, rrect, fmt, MONTH_NAMES, BIFACIAL,
    MONTHLY_DAILY_KWH_PER_KWP, SOLAR_SHAPE, LOAD_SHAPE, MONTHLY_LOAD_FACTOR, DAYS_IN_MONTH)

EP=0.34; DEG=0.005; ESC=0.025
C_ORANGE=HexColor("#E8730C")

# ---- Simulation (Zwei-String-Topologie) ----
def sim(modules_dc, modules_ac, battery_kwh, consumption, smart=True, ep=EP,
        module_wp=445, bifacial=1.03, max_house_w=800, max_2nd_inv_w=800,
        ac_in_cap_w=1000, dc_charge_w=1200, batt_throughput_w=1440, blind_match=0.78):
    kwp_A=modules_dc*module_wp/1000; kwp_B=modules_ac*module_wp/1000
    sys_eff=0.95; inv_eff=0.96; ce_dc=0.96; ce_ac=0.90; de=0.94
    min_soc=battery_kwh*0.10; soc=battery_kwh*0.15
    house_cap=max_house_w/1000; dc_chg_cap=dc_charge_w/1000
    ac_chg_cap=min(max_2nd_inv_w,ac_in_cap_w)/1000; bt_cap=batt_throughput_w/1000
    ss=sum(SOLAR_SHAPE); ns=[s/ss for s in SOLAR_SHAPE]; ls=sum(LOAD_SHAPE)
    lfw=sum(d*f for d,f in zip(DAYS_IN_MONTH,MONTHLY_LOAD_FACTOR))
    CF,CM,CLM=0.40,1.45,0.70
    T={k:0.0 for k in['gen_dc','self','feed','grid','curt']}; monthly=[]
    for m in range(12):
        days=DAYS_IN_MONTH[m]
        dA=MONTHLY_DAILY_KWH_PER_KWP[m]*kwp_A*sys_eff*bifacial
        dB=MONTHLY_DAILY_KWH_PER_KWP[m]*kwp_B*sys_eff*bifacial
        dload=(consumption/lfw)*MONTHLY_LOAD_FACTOR[m]
        Mo={k:0.0 for k in T}; cd=round(days*CF); cl=days-cd
        for nd,mult in[(cd,CM),(cl,CLM)]:
            for _ in range(nd):
                for h in range(24):
                    pvA=dA*mult*ns[h]; pvB=dB*mult*ns[h]
                    load=dload*(LOAD_SHAPE[h]/ls)
                    T['gen_dc']+=pvA+pvB; Mo['gen_dc']+=pvA+pvB; bt=bt_cap
                    direct=min(pvA*inv_eff,load,house_cap)
                    served=direct; pvA_r=pvA-direct/inv_eff; lrem=load-served
                    if battery_kwh>0:
                        sp=battery_kwh-soc
                        dc=min(pvA_r,dc_chg_cap,bt,sp/ce_dc); soc+=dc*ce_dc; pvA_r-=dc; bt-=dc
                        sp=battery_kwh-soc; bav=min(pvB,ac_chg_cap)
                        ac=min(bav,bt,sp/ce_ac); soc+=ac*ce_ac; bt-=ac; curtB=pvB-ac
                    else: curtB=pvB
                    curtA=pvA_r
                    if battery_kwh>0 and lrem>1e-4:
                        av=max(0,soc-min_soc); hd=house_cap-served
                        dis=min(lrem/de,av,hd/inv_eff if hd>0 else 0); soc-=dis; aco=dis*de
                        if smart: served+=aco; lrem-=aco
                        else:
                            hit=aco*blind_match; served+=hit; lrem-=hit
                            T['feed']+=aco-hit; Mo['feed']+=aco-hit
                    T['self']+=served; Mo['self']+=served
                    T['grid']+=max(0,lrem); Mo['grid']+=max(0,lrem)
                    T['curt']+=curtA+curtB; Mo['curt']+=curtA+curtB
        monthly.append(Mo)
    gen_ac=T['gen_dc']*inv_eff
    return dict(gen_dc=round(T['gen_dc']),self=round(T['self']),grid=round(T['grid']),
        feed=round(T['feed']),curt=round(T['curt']),
        autarky=round(T['self']/consumption*100,1),
        self_rate=round(T['self']/gen_ac*100,1) if gen_ac>0 else 0,
        savings=round(T['self']*ep),monthly=monthly,kwp=kwp_A+kwp_B,battery=battery_kwh)

def econ(extra_self, price, ep=EP):
    cum=0; amort=None; yearly=[]
    for y in range(1,26):
        ys=extra_self*(1-DEG)**(y-1)*ep*(1+ESC)**(y-1); cum+=ys
        yearly.append(cum)
        if amort is None and cum>=price: amort=y
    return amort, round(cum-price), round(cum), yearly

def econ_combined(extra_self, price, flat_eur, ep=EP):
    cum=0
    for y in range(1,26):
        cum+=extra_self*(1-DEG)**(y-1)*ep*(1+ESC)**(y-1)+flat_eur*(1+ESC)**(y-1)
        if cum>=price: return y, round(cum-price)
    return None, round(cum-price)

# ---- Topologie-Schema ----
def draw_topology(c, x, y, w, h, added_modules=4, n_batt=3):
    import math
    rrect(c,x,y,w,h,3*mm,C_WHITE,HexColor("#D1D5DB"))
    c.setFillColor(C_PRIMARY); c.setFont("Helvetica-Bold",8)
    c.drawString(x+5*mm,y+h-6.5*mm,f"So funktioniert Ihr {4+added_modules}-Modul-System")
    def box(bx,by,bw,bh,txt,sub,fill,fg=C_WHITE):
        rrect(c,bx,by,bw,bh,1.5*mm,fill)
        c.setFillColor(fg); c.setFont("Helvetica-Bold",6.5)
        c.drawCentredString(bx+bw/2,by+bh-4.3*mm,txt)
        if sub:
            c.setFont("Helvetica",5.2); c.drawCentredString(bx+bw/2,by+1.7*mm,sub)
    def arrow(x1,y1,x2,y2,lbl=None,col=C_GRAY,lbldy=1.4):
        c.setStrokeColor(col); c.setLineWidth(1.1); c.line(x1,y1,x2,y2)
        ang=math.atan2(y2-y1,x2-x1)
        for da in (2.7,-2.7):
            c.line(x2,y2,x2-4*math.cos(ang+da),y2-4*math.sin(ang+da))
        if lbl:
            c.setFillColor(col); c.setFont("Helvetica-Bold",5)
            c.drawCentredString((x1+x2)/2,(y1+y2)/2+lbldy*mm,lbl)
    bh=9*mm; bw=23*mm
    cy_top=y+h-16*mm; cy_bot=y+11*mm
    # Module links
    box(x+6*mm, cy_top-bh/2, bw,bh,"4 Module","Bestand (DC)",C_PRIMARY)
    box(x+6*mm, cy_bot-bh/2, bw,bh,f"{added_modules} Module","neu",C_ACCENT_DARK)
    inv_x=x+6*mm+bw+13*mm
    box(inv_x, cy_bot-bh/2, 22*mm,bh,"800-W-WR","2. Wechselr.",C_BLUE)
    # SolarFlow mittig, hoch
    sf_w=32*mm; sf_x=x+w*0.55; sf_y=y+9*mm; sf_h=h-18*mm
    rrect(c,sf_x,sf_y,sf_w,sf_h,2*mm,C_PRIMARY)
    c.setFillColor(C_WHITE); c.setFont("Helvetica-Bold",7.5)
    c.drawCentredString(sf_x+sf_w/2,sf_y+sf_h-7*mm,"SolarFlow")
    c.setFont("Helvetica",5.4); c.drawCentredString(sf_x+sf_w/2,sf_y+sf_h-12*mm,"800 Pro")
    c.drawCentredString(sf_x+sf_w/2,sf_y+4*mm,"Hub + Akku")
    # rechts
    rx=x+w-28*mm
    box(rx, cy_top-bh/2, 23*mm,bh,"Haus","max. 800 W",C_ACCENT_DARK)
    box(rx, cy_bot-bh/2, 23*mm,bh,"Akku",f"{n_batt}\xd7 1,92 kWh",HexColor("#374151"))
    # Pfeile
    arrow(x+6*mm+bw, cy_top, sf_x, sf_y+sf_h-5*mm,"DC",C_ACCENT_DARK)
    arrow(x+6*mm+bw, cy_bot, inv_x, cy_bot,col=C_PRIMARY)
    arrow(inv_x+22*mm, cy_bot, sf_x, sf_y+5*mm,"AC-Eingang",C_BLUE)
    arrow(sf_x+sf_w, sf_y+sf_h-5*mm, rx, cy_top,"800 W",C_ACCENT_DARK)
    arrow(sf_x+sf_w, sf_y+5*mm, rx, cy_bot,col=HexColor("#374151"))
    c.setFillColor(C_GRAY); c.setFont("Helvetica-Oblique",5.8)
    c.drawString(x+5*mm,y+3.2*mm,"Netzeinspeisung bleibt bei 800 W \u2013 ein 800-W-Steckersolarger\xe4t. "
                 "Der 2. String l\xe4dt \xfcber den AC-Eingang nur den Akku.")

# ---- Monatschart Vorher/Nachher ----
def draw_month_bars(c,x,y,w,h,ist,neu):
    mx=max(max(d['self'] for d in neu['monthly']),max(d['self'] for d in ist['monthly']))*1.15
    gw=w/12; bw=gw*0.32
    c.setStrokeColor(HexColor("#E5E7EB")); c.setLineWidth(0.2)
    for f in[0,.25,.5,.75,1]:
        gy=y+f*h; c.line(x,gy,x+w,gy)
        c.setFillColor(C_GRAY); c.setFont("Helvetica",4.5); c.drawRightString(x-1.5*mm,gy-1,f"{f*mx:.0f}")
    for mi in range(12):
        gx=x+mi*gw
        c.setFillColor(C_GRAY); c.setFont("Helvetica",5); c.drawCentredString(gx+gw/2,y-3.5*mm,MONTH_NAMES[mi])
        for ci,(cfg,col) in enumerate([(ist,HexColor("#9CA3AF")),(neu,C_ACCENT_DARK)]):
            v=cfg['monthly'][mi]['self']; bh=(v/mx)*h if mx>0 else 0
            bx=gx+gw*0.18+ci*(bw+1*mm)
            c.setFillColor(col); c.rect(bx,y,bw,bh,fill=1,stroke=0)
    ly=y-8*mm
    for lb,col in [("IST (4 Module)",HexColor("#9CA3AF")),("NEU (8 Module)",C_ACCENT_DARK)]:
        c.setFillColor(col); c.rect(x+( 0 if "IST" in lb else 42*mm),ly,3*mm,2.5*mm,fill=1,stroke=0)
        c.setFillColor(C_GRAY); c.setFont("Helvetica",6)
        c.drawString(x+(0 if "IST" in lb else 42*mm)+4*mm,ly+0.3*mm,lb)

# ---- Amortisationskurve (Delta) ----
def draw_amort(c,x,y,w,h,yearly,price):
    rrect(c,x-4*mm,y-6*mm,w+8*mm,h+16*mm,3*mm,C_WHITE,HexColor("#D1D5DB"))
    c.setFillColor(C_DARK); c.setFont("Helvetica-Bold",8)
    c.drawString(x,y+h+6*mm,"Kumulierte Mehr-Ersparnis vs. Investition")
    scale=max(max(yearly),price)*1.1
    c.setStrokeColor(HexColor("#E5E7EB")); c.setLineWidth(0.2)
    for f in[0,.25,.5,.75,1]:
        gy=y+f*h; c.line(x,gy,x+w,gy)
        c.setFillColor(C_GRAY); c.setFont("Helvetica",5); c.drawRightString(x-2*mm,gy-1.5,f"{f*scale/1000:.0f}k")
    for yr in[1,5,10,15,20,25]:
        px=x+((yr-1)/24)*w; c.setFillColor(C_GRAY); c.setFont("Helvetica",5); c.drawCentredString(px,y-3.5*mm,f"J{yr}")
    cy=y+(price/scale)*h
    c.setStrokeColor(C_RED); c.setLineWidth(0.5); c.setDash(2,2); c.line(x,cy,x+w,cy); c.setDash()
    c.setFillColor(C_RED); c.setFont("Helvetica-Bold",5.5); c.drawString(x+1*mm,cy+1*mm,f"Investition {fmt(price)} EUR")
    c.setStrokeColor(C_ACCENT_DARK); c.setLineWidth(1.6); p=c.beginPath()
    for j,v in enumerate(yearly):
        px=x+(j/24)*w; py=y+(v/scale)*h
        p.moveTo(px,py) if j==0 else p.lineTo(px,py)
    c.drawPath(p)
    for j,v in enumerate(yearly):
        if v>=price:
            px=x+(j/24)*w; py=y+(v/scale)*h
            c.setFillColor(C_ACCENT_DARK); c.circle(px,py,2.3,fill=1,stroke=0)
            c.setStrokeColor(C_WHITE); c.setLineWidth(1); c.circle(px,py,2.3,fill=0,stroke=1); break

# ===================================================================
def generate_upgrade_report(customer, baseline_battery=1.92, target_modules=8,
                            add_ab2000_std=2, add_ab2000_ent=1,
                            upgrade_price=4448, entry_price=3848, smart_before=False,
                            montage="Schraegdach", electricity_price=0.34,
                            action_registration=350, action_deadline="31.07.2026",
                            dyn_tariff_arb=None, out_path="upgrade_bericht.pdf"):
    bif=BIFACIAL[montage]; cons=customer["consumption"]
    added_modules=target_modules-4
    add_ab2000_std=max(1,add_ab2000_std); add_ab2000_ent=max(1,add_ab2000_ent)  # min. 1 (SolarFlow)
    total_std=baseline_battery+add_ab2000_std*1.92
    total_ent=baseline_battery+add_ab2000_ent*1.92
    n_batt=round(total_std/1.92)
    ist=sim(4,0,baseline_battery,cons,smart=smart_before,bifacial=bif,ep=electricity_price)
    neu=sim(4,added_modules,total_std,cons,smart=True,bifacial=bif,ep=electricity_price)
    nge=sim(4,added_modules,total_ent,cons,smart=True,bifacial=bif,ep=electricity_price)
    extra_self=neu['self']-ist['self']; extra_self_e=nge['self']-ist['self']
    price_std=upgrade_price-action_registration
    price_ent=entry_price-action_registration
    amort,profit25,cum25,yearly=econ(extra_self,price_std,ep=electricity_price)
    amort_e,profit25_e,cum25_e,_=econ(extra_self_e,price_ent,ep=electricity_price)
    extra_y1=round(extra_self*electricity_price); extra_y1_e=round(extra_self_e*electricity_price)
    avg_extra_year=round(cum25/25); avg_extra_year_e=round(cum25_e/25)
    avg25=electricity_price*(sum((1+ESC)**(y-1) for y in range(1,26))/25)
    if dyn_tariff_arb is None:
        dyn_tariff_arb=round(0.9*total_std*150*0.13)
    amort_arb,profit_arb=econ_combined(extra_self,price_std,dyn_tariff_arb,electricity_price)
    co2_factor=0.38
    co2_std=round(extra_self*co2_factor/10)*10
    co2_ent=round(extra_self_e*co2_factor/10)*10
    ml={"Schraegdach":"Schr\xe4gdach","Flachdach":"Flachdach/Aufst\xe4nderung"}[montage]

    # Empfohlene Variante = h\xf6herer Gewinn \xfcber 25 Jahre (nicht pauschal die gr\xf6\xdfere Speicher-Variante)
    std_wins=profit25>=profit25_e
    n_batt_ent=round(total_ent/1.92)
    reco_neu=neu if std_wins else nge
    reco_total_battery=total_std if std_wins else total_ent
    reco_n_batt=n_batt if std_wins else n_batt_ent
    reco_price=price_std if std_wins else price_ent
    reco_extra_self=extra_self if std_wins else extra_self_e
    reco_extra_y1=extra_y1 if std_wins else extra_y1_e
    reco_avg_extra_year=avg_extra_year if std_wins else avg_extra_year_e
    reco_co2=co2_std if std_wins else co2_ent
    reco_profit25=profit25 if std_wins else profit25_e
    reco_title=f"{n_batt}\xd7 Akku" if std_wins else f"{n_batt_ent}\xd7 Akku"
    total_savings_25=econ(reco_neu['self'],0,electricity_price)[2]

    out=out_path
    pdf=canvas.Canvas(out,pagesize=A4); tp=3

    # ===== SEITE 1 =====
    draw_header(pdf,1,tp); draw_footer(pdf)
    y=H-42*mm
    pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Bold",22)
    pdf.drawString(20*mm,y,"Ihr Erweiterungs-Potenzial"); y-=9*mm
    pdf.setFillColor(C_PRIMARY); pdf.drawString(20*mm,y,f"Von 4 auf {target_modules} Module")
    y-=5*mm; pdf.setFillColor(C_ACCENT); pdf.rect(20*mm,y,40*mm,1*mm,fill=1,stroke=0)
    y-=8*mm; pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",8)
    pdf.drawString(20*mm,y,"Erweiterungs-Empfehlung f\xfcr Ihr bestehendes SolarFlow-System  \xb7  Berichts-Nr. MSF-U-2026")

    y-=12*mm; bh=26*mm
    rrect(pdf,20*mm,y-bh,W-40*mm,bh,3*mm,C_BG_LIGHT,C_PRIMARY)
    pdf.setFillColor(C_PRIMARY); pdf.setFont("Helvetica-Bold",9); pdf.drawString(26*mm,y-5*mm,"Objektdaten")
    pdf.setFillColor(C_DARK); pdf.setFont("Helvetica",8)
    pdf.drawString(26*mm,y-12*mm,f"Eigent\xfcmer:  {customer['name']}")
    pdf.drawString(26*mm,y-18*mm,f"Adresse:  {customer['street']}, {customer['city']}")
    pdf.drawString(26*mm,y-24*mm,f"Aktuell:  4\xd7 445 Wp + {baseline_battery:.2f} kWh"
                   f"{'  ohne Smart Meter' if not smart_before else ''}")
    pdf.drawString(112*mm,y-12*mm,f"Jahresverbrauch:  {fmt(cons)} kWh")
    pdf.drawString(112*mm,y-18*mm,f"Ausrichtung:  {customer['orientation']}  \xb7  {ml}")
    pdf.drawString(112*mm,y-24*mm,f"Strompreis:  {electricity_price:.2f} EUR/kWh  (\xd8 {avg25:.2f} \xfcber 25 J.)")

    # Topologie
    y-=bh+8*mm; th=40*mm
    draw_topology(pdf,20*mm,y-th,W-40*mm,th,added_modules,reco_n_batt)
    y-=th

    # KPI-Strip (Zahlen der empfohlenen Variante, siehe Wirtschaftlichkeits-Vergleich S.3)
    y-=8*mm; kh=25*mm; kw=(W-40*mm-9*mm)/4
    kpis=[("Autarkie",f"{ist['autarky']:.0f}% \u2192 {reco_neu['autarky']:.0f}%",C_ACCENT_DARK),
          ("Mehr-Eigenverbrauch",f"+{fmt(reco_extra_self)} kWh/J",C_PRIMARY),
          ("__ERSPARNIS__",None,C_BLUE),
          ("Zus\xe4tzl. Gewinn (25 J.)",f"+{fmt(reco_profit25)} EUR",C_ACCENT_DARK)]
    for i,(lab,val,col) in enumerate(kpis):
        bx=20*mm+i*(kw+3*mm)
        rrect(pdf,bx,y-kh,kw,kh,2*mm,C_BG_ACCENT,col)
        if lab=="__ERSPARNIS__":
            pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6.3); pdf.drawCentredString(bx+kw/2,y-6*mm,"Mehr-Ersparnis")
            pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6); pdf.drawString(bx+4*mm,y-13*mm,"1. Jahr")
            pdf.setFillColor(col); pdf.setFont("Helvetica-Bold",9); pdf.drawRightString(bx+kw-4*mm,y-13*mm,f"+{fmt(reco_extra_y1)} EUR")
            pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6); pdf.drawString(bx+4*mm,y-19*mm,"\xd8 25 Jahre")
            pdf.setFillColor(col); pdf.setFont("Helvetica-Bold",9); pdf.drawRightString(bx+kw-4*mm,y-19*mm,f"+{fmt(reco_avg_extra_year)} EUR/J")
        else:
            pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6.3); pdf.drawCentredString(bx+kw/2,y-6.5*mm,lab)
            pdf.setFillColor(col); pdf.setFont("Helvetica-Bold",12); pdf.drawCentredString(bx+kw/2,y-15.5*mm,val)
    y-=kh
    # Gesamt-Ersparnis der Anlage
    y-=4*mm; gh=9*mm
    rrect(pdf,20*mm,y-gh,W-40*mm,gh,2*mm,C_PRIMARY)
    pdf.setFillColor(C_WHITE); pdf.setFont("Helvetica",7.5)
    pdf.drawString(26*mm,y-5.8*mm,f"Gesamt-Ersparnis Ihrer {target_modules}-Modul-Anlage \xfcber 25 Jahre:")
    pdf.setFont("Helvetica-Bold",9.5); pdf.drawRightString(W-26*mm,y-5.8*mm,f"rund {fmt(round(total_savings_25/500)*500)} EUR")
    y-=gh

    # Intro
    y-=9*mm; pdf.setFillColor(C_DARK); pdf.setFont("Helvetica",8)
    for ln in [
        f"Sehr geehrter Herr {customer['name'].split()[-1]},",
        "",
        "Ihr 4-Modul-System st\xf6\xdft mittags an die 800-W-Grenze, und ohne Smart Meter entl\xe4dt der",
        f"Akku nicht lastgef\xfchrt. {added_modules} weitere Module steigern Ihre Erzeugung deutlich; gr\xf6\xdferer",
        "Akku und Smart Meter wandeln den \xdcberschuss ganzj\xe4hrig in nutzbaren Strom. Die Anlage bleibt",
        "dabei ein 800-W-Steckersolarger\xe4t \u2013 die vereinfachte Anmeldung \xfcbernehmen wir f\xfcr Sie.",
    ]:
        pdf.drawString(20*mm,y,ln); y-=4.2*mm

    # Vorteils-Box
    y-=3*mm; vh=46*mm
    rrect(pdf,20*mm,y-vh,W-40*mm,vh,3*mm,C_BG_ACCENT,C_ACCENT_DARK)
    pdf.setFillColor(C_PRIMARY); pdf.setFont("Helvetica-Bold",9)
    pdf.drawString(26*mm,y-6*mm,"Ihre neuen Vorteile durch das Upgrade")
    def _chk(cx,cy):
        pdf.setStrokeColor(C_ACCENT_DARK); pdf.setLineWidth(1.5)
        pdf.line(cx,cy,cx+1.3*mm,cy-1.4*mm); pdf.line(cx+1.3*mm,cy-1.4*mm,cx+3.6*mm,cy+1.8*mm)
    vben=[("Neuer SolarFlow 800 Pro Hybrid-Wechselrichter","Das Herzst\xfcck Ihres Systems: Hybrid-WR mit MPPT, AC-Eingang und Akku-Management."),
          ("Intelligente Einspeisung","Smart Meter steuert die Abgabe lastgenau \u2013 kein Solarstrom wird mehr verschenkt."),
          ("Notstromfunktion","Bei Stromausfall versorgt die Off-Grid-Steckdose wichtige Ger\xe4te (bis 1000 W, < 20 ms)."),
          ("Bereit f\xfcr dynamische Tarife","Akku l\xe4dt bei g\xfcnstigen Preisen, entl\xe4dt bei teuren \u2013 zus\xe4tzliche Ersparnis."),
          ("Aktiver Klimaschutz",f"Vermeidet rund {fmt(reco_co2)} kg CO2 pro Jahr \u2013 sauberer Solarstrom statt Netzbezug.")]
    vy=y-11.5*mm
    for t,d in vben:
        _chk(27*mm,vy+0.5*mm)
        pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Bold",7.3); pdf.drawString(33*mm,vy,t)
        pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6.5); pdf.drawString(33*mm,vy-3.4*mm,d)
        vy-=6.7*mm
    pdf.showPage()

    # ===== SEITE 2 =====
    draw_header(pdf,2,tp); draw_footer(pdf)
    y=H-40*mm
    pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Bold",13); pdf.drawString(20*mm,y,"Vorher / Nachher im Detail"); y-=6*mm
    pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",7.5)
    pdf.drawString(20*mm,y,"Stundengenaue Simulation (8.760 h/a) mit Zwei-String-Topologie und 800-W-Ausgang"); y-=9*mm

    rows=[("Module / Leistung",f"4\xd7 445 Wp ({ist['kwp']:.2f} kWp)",f"{target_modules}\xd7 445 Wp ({reco_neu['kwp']:.2f} kWp)",False),
          ("Speicher",f"{baseline_battery:.2f} kWh",f"{reco_total_battery:.2f} kWh",False),
          ("Smart Meter / lastgef\xfchrt","Nein" if not smart_before else "Ja","Ja",False),
          ("Jahresertrag (DC)",f"{fmt(ist['gen_dc'])} kWh",f"{fmt(reco_neu['gen_dc'])} kWh",False),
          ("Eigenverbrauch",f"{fmt(ist['self'])} kWh",f"{fmt(reco_neu['self'])} kWh",True),
          ("Autarkiegrad",f"{ist['autarky']:.0f}%",f"{reco_neu['autarky']:.0f}%",True),
          ("Netzbezug (Rest)",f"{fmt(ist['grid'])} kWh",f"{fmt(reco_neu['grid'])} kWh",False)]
    tx=20*mm; cw=[58*mm,46*mm,46*mm]; rh=7*mm
    pdf.setFillColor(C_PRIMARY); pdf.rect(tx,y,sum(cw),rh,fill=1,stroke=0)
    pdf.setFillColor(C_WHITE); pdf.setFont("Helvetica-Bold",7)
    pdf.drawString(tx+2.5*mm,y+2.5*mm,"Kennzahl")
    pdf.drawCentredString(tx+cw[0]+cw[1]/2,y+2.5*mm,"IST  (4 Module)")
    pdf.drawCentredString(tx+cw[0]+cw[1]+cw[2]/2,y+2.5*mm,f"NEU  ({target_modules} Module)")
    for i,(lab,va,vb,bold) in enumerate(rows):
        ry=y-(i+1)*rh
        if i%2==0: pdf.setFillColor(HexColor("#F9FAFB")); pdf.rect(tx,ry,sum(cw),rh,fill=1,stroke=0)
        pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Bold" if bold else "Helvetica",7)
        pdf.drawString(tx+2.5*mm,ry+2.3*mm,lab)
        pdf.setFillColor(C_GRAY if bold else C_DARK); pdf.setFont("Helvetica",7)
        pdf.drawCentredString(tx+cw[0]+cw[1]/2,ry+2.3*mm,va)
        pdf.setFillColor(C_ACCENT_DARK if bold else C_DARK); pdf.setFont("Helvetica-Bold" if bold else "Helvetica",7)
        pdf.drawCentredString(tx+cw[0]+cw[1]+cw[2]/2,ry+2.3*mm,vb)
    th=(len(rows)+1)*rh
    pdf.setStrokeColor(HexColor("#D1D5DB")); pdf.setLineWidth(0.4); pdf.rect(tx,y-th+rh,sum(cw),th,fill=0,stroke=1)
    y=y-th

    # Insight
    y-=8*mm; ih=20*mm
    rrect(pdf,20*mm,y-ih,W-40*mm,ih,2*mm,C_BG_ACCENT,C_ACCENT_DARK)
    pdf.setFillColor(C_PRIMARY); pdf.setFont("Helvetica-Bold",8); pdf.drawString(26*mm,y-6*mm,"Wo der Mehrwert entsteht")
    pdf.setFillColor(C_DARK); pdf.setFont("Helvetica",7)
    pdf.drawString(26*mm,y-12*mm,"Der zweite String steigert die Erzeugung deutlich; erst dadurch entsteht genug \xdcberschuss, den Akku und")
    pdf.drawString(26*mm,y-17*mm,"Smart Meter in Eigenverbrauch wandeln. Der Zugewinn ist ganzj\xe4hrig \u2013 am gr\xf6\xdften in den sonnenreichen Monaten.")
    y-=ih

    # Monatschart
    y-=10*mm; ch=40*mm
    pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Bold",8); pdf.drawString(20*mm,y,"Monatlicher Eigenverbrauch (kWh)")
    draw_month_bars(pdf,30*mm,y-5*mm-ch,W-50*mm,ch,ist,reco_neu)
    pdf.showPage()

    # ===== SEITE 3 =====
    draw_header(pdf,3,tp); draw_footer(pdf)
    y=H-38*mm
    pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Bold",13); pdf.drawString(20*mm,y,"Wirtschaftlichkeit & Empfehlung"); y-=9*mm

    # Aktions-Banner (Datum in Dunkelblau hervorgehoben)
    y-=2*mm; ah=11*mm
    rrect(pdf,20*mm,y-ah,W-40*mm,ah,2*mm,C_ORANGE)
    part1=f"Aktion bis {action_deadline}:"
    pdf.setFont("Helvetica-Bold",8.5); w1=pdf.stringWidth(part1,"Helvetica-Bold",8.5)
    pdf.setFillColor(C_PRIMARY); pdf.drawString(26*mm,y-4.5*mm,part1)
    pdf.setFillColor(C_WHITE); pdf.drawString(26*mm+w1+1.5*mm,y-4.5*mm,"Wir \xfcbernehmen die Anmeldung")
    pdf.setFont("Helvetica",7.5)
    pdf.drawString(26*mm,y-8.8*mm,f"Wert {action_registration} EUR \u2013 f\xfcr Bestandskunden kostenfrei. Die Aktionspreise unten enthalten den Vorteil bereits.")
    y-=ah+8*mm

    # Zwei Varianten-Karten – \"EMPFOHLEN\" erh\xe4lt, wer in 25 Jahren den h\xf6heren Gewinn bringt
    cw=(W-40*mm-6*mm)/2; chh=51*mm
    variants=[(std_wins,f"{n_batt}\xd7 Akku",f"+ {added_modules} Module + {add_ab2000_std}\xd7 1,92 kWh Speicher + Smart Meter",
               upgrade_price,price_std,neu['autarky'],extra_y1,avg_extra_year,co2_std,profit25,C_PRIMARY),
              (not std_wins,f"{n_batt_ent}\xd7 Akku",f"+ {added_modules} Module + {add_ab2000_ent}\xd7 1,92 kWh Speicher + Smart Meter",
               entry_price,price_ent,nge['autarky'],extra_y1_e,avg_extra_year_e,co2_ent,profit25_e,C_BLUE)]
    for i,(reco,title,sub,lst,act,aut,y1,avg,co,pf,col) in enumerate(variants):
        badge="MEHR GEWINN" if reco else None
        bx=20*mm+i*(cw+6*mm)
        rrect(pdf,bx,y-chh,cw,chh,3*mm,C_BG_ACCENT if reco else C_WHITE,col)
        if badge:
            tw=pdf.stringWidth(badge,"Helvetica-Bold",6)+6*mm
            pdf.setFillColor(col); pdf.roundRect(bx+cw/2-tw/2,y-2*mm,tw,5*mm,2*mm,fill=1,stroke=0)
            pdf.setFillColor(C_WHITE); pdf.setFont("Helvetica-Bold",6); pdf.drawCentredString(bx+cw/2,y-0.5*mm,badge)
        pdf.setFillColor(col); pdf.setFont("Helvetica-Bold",10); pdf.drawCentredString(bx+cw/2,y-9*mm,title)
        pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6.3); pdf.drawCentredString(bx+cw/2,y-13.5*mm,sub)
        pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6.5); pdf.drawCentredString(bx+cw/2,y-18.5*mm,f"statt {fmt(lst)} EUR")
        pdf.setFillColor(col); pdf.setFont("Helvetica-Bold",15); pdf.drawCentredString(bx+cw/2,y-25.5*mm,f"{fmt(act)} EUR")
        pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",5.5); pdf.drawCentredString(bx+cw/2,y-29*mm,"Aktionspreis, Anmeldung inkl.")
        mvy=y-35*mm
        for lab,val in [("Autarkie",f"{aut:.0f}%"),("Mehr-Ersparnis 1. Jahr",f"+{fmt(y1)} EUR"),
                        ("\xd8 Mehr-Ersparnis/J (25 J.)",f"+{fmt(avg)} EUR"),
                        ("CO2-Einsparung/Jahr",f"{fmt(co)} kg"),("Gewinn 25 Jahre",f"+{fmt(pf)} EUR")]:
            pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6.3); pdf.drawString(bx+6*mm,mvy,lab)
            pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Bold",6.3); pdf.drawRightString(bx+cw-6*mm,mvy,val)
            mvy-=3.3*mm
    y-=chh+6*mm

    # Arbitrage + Ø-Preis
    pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Oblique",7)
    pdf.drawString(20*mm,y,f"+ Mit dynamischem Stromtarif zus\xe4tzlich ca. {dyn_tariff_arb} EUR/Jahr durch Lade-Arbitrage "
                   f"(konservativ gesch\xe4tzt, oben nicht enthalten).")
    y-=5*mm
    pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",6.5)
    pdf.drawString(20*mm,y,f"Ersparnis bewertet mit \xd8 {avg25:.2f} EUR/kWh \xfcber 25 Jahre (Strompreis heute {electricity_price:.2f} EUR/kWh, +2,5%/Jahr).")
    y-=8*mm

    # Empfehlung
    rh2=27*mm
    rrect(pdf,20*mm,y-rh2,W-40*mm,rh2,4*mm,C_PRIMARY)
    pdf.setFillColor(C_WHITE); pdf.setFont("Helvetica-Bold",10); pdf.drawString(28*mm,y-7*mm,"Unsere Empfehlung")
    pdf.setFillColor(C_ACCENT); pdf.setFont("Helvetica-Bold",8)
    pdf.drawString(28*mm,y-14*mm,f"{reco_title}: {ist['autarky']:.0f}% \u2192 {reco_neu['autarky']:.0f}% Autarkie f\xfcr {fmt(reco_price)} EUR (Aktion)")
    pdf.setFillColor(C_WHITE); pdf.setFont("Helvetica",7.5)
    pdf.drawString(28*mm,y-20*mm,f"+{fmt(reco_extra_self)} kWh/Jahr mehr Eigenverbrauch, +{fmt(reco_profit25)} EUR Gewinn in 25 Jahren \u2013 dazu")
    pdf.drawString(28*mm,y-24.5*mm,"Notstrom, intelligente Einspeisung und die Basis f\xfcr dynamische Tarife.")
    y-=rh2+6*mm

    # CTA
    cta=21*mm
    rrect(pdf,20*mm,y-cta,W-40*mm,cta,4*mm,C_BG_ACCENT,C_ACCENT_DARK)
    pdf.setFillColor(C_DARK); pdf.setFont("Helvetica-Bold",10); pdf.drawString(28*mm,y-7*mm,"Sichern Sie sich die Aktion")
    pdf.setFont("Helvetica",7.5)
    pdf.drawString(28*mm,y-13*mm,f"Kostenloses Beratungsgespr\xe4ch bis {action_deadline}:")
    pdf.drawString(28*mm,y-18*mm,"kontakt@mysolarfuture.de  \xb7  www.mysolarfuture.de")
    y-=cta+5*mm

    pdf.setFillColor(C_GRAY); pdf.setFont("Helvetica",5)
    for ln in["Simulation, keine Ertragsgarantie. PR 95%, Bifazial +3% (Schr\xe4gdach). Strompreissteigerung 2,5% p.a., Degradation 0,5% p.a.",
              f"Aktion: Anmeldung (Wert {action_registration} EUR) f\xfcr Bestandskunden bis {action_deadline} kostenfrei. 800-W-Steckersolar; Registrierung im Marktstammdatenregister erforderlich \u2013 \xfcbernehmen wir.",
              "Arbitrage-Sch\xe4tzung nur mit dynamischem Tarif. Akku-Erweiterung per AB2000. Preise inkl. MwSt. (0% PV gem. UStG). Freibleibend."]:
        pdf.drawString(20*mm,y,ln); y-=3*mm
    pdf.save()

    print(f"OK: {customer['name']}, {cons} kWh | empfohlen: {reco_title} ({'Standard' if std_wins else 'Einstieg'}) | "
          f"IST Aut {ist['autarky']}% / NEU {reco_neu['autarky']}% | "
          f"+{reco_extra_self} kWh, +{reco_extra_y1} EUR/J | Gewinn25 +{reco_profit25} EUR "
          f"(Standard +{profit25} EUR vs. Einstieg +{profit25_e} EUR) | Abregel NEU {reco_neu['curt']}")
    return out

if __name__=="__main__":
    generate_upgrade_report(
        customer={"name":"Max Mustermann","street":"Musterstr. 5","city":"27755 Delmenhorst",
                  "consumption":4500,"orientation":"S\xfcd"},
        baseline_battery=1.92, target_modules=8, add_ab2000_std=2, add_ab2000_ent=1,
        upgrade_price=4448, entry_price=3848, smart_before=False, montage="Schraegdach")
