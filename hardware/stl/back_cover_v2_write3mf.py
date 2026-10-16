"""Write the reworked back cover mesh into the original Bambu project.

Usage: back_cover_v2_write3mf.py ORIGINAL.3mf CAGE_BAY.stl OUT.3mf
ORIGINAL is the unmodified MakerWorld project: git show 1e82a6f:hardware/stl/back_cover_v2.3mf
"""
import sys, zipfile, re, numpy as np, trimesh, io, datetime
from PIL import Image, ImageDraw
SRC=sys.argv[1]
OUT=sys.argv[3]
t=trimesh.load(sys.argv[2])
V=np.asarray(t.vertices).copy(); V[:,2]+=1.25          # STL -> 3MF object-local
F=np.asarray(t.faces)
zin=zipfile.ZipFile(SRC)
def render(size, view='iso'):
    # print orientation (item transform: y,z flipped) seen from an isometric angle
    P=V*np.array([1,-1,-1])
    a=np.radians(-35); b=np.radians(30)
    Rz=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    Rx=np.array([[1,0,0],[0,np.cos(b),-np.sin(b)],[0,np.sin(b),np.cos(b)]]) if view=='iso' else np.eye(3)
    Q=P@Rz.T@Rx.T if view=='iso' else P
    tri=Q[F]; n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); n/=np.linalg.norm(n,axis=1)[:,None]+1e-12
    vis=n[:,2]>0 if view=='iso' else n[:,2]>0
    light=np.array([0.3,0.5,0.8]); light/=np.linalg.norm(light)
    shade=np.clip(n@light,0,1)
    order=np.argsort(tri[:,:,2].mean(1))
    lo=Q[:,:2].min(0); hi=Q[:,:2].max(0); s=(size*0.86)/max(hi-lo); off=(size-(hi-lo)*s)/2
    im=Image.new('RGB',(size,size),(0,0,0) if size>300 else (255,255,255)); d=ImageDraw.Draw(im)
    for i in order:
        if not vis[i]: continue
        c=int(70+150*shade[i])
        pts=[((p[0]-lo[0])*s+off[0], size-((p[1]-lo[1])*s+off[1])) for p in tri[i]]
        d.polygon(pts,fill=(c,c,c))
    buf=io.BytesIO(); im.save(buf,'PNG'); return buf.getvalue()
zout=zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED)
today=datetime.date.today().isoformat()
for info in zin.infolist():
    data=zin.read(info.filename)
    n=info.filename
    if n=='3D/Objects/object_1.model':
        txt=data.decode()
        head=txt[:txt.index('<vertices>')]
        tail=txt[txt.index('</triangles>'):]
        vs='\n'.join(f'     <vertex x="{x:.6g}" y="{y:.6g}" z="{z:.6g}"/>' for x,y,z in V)
        ts='\n'.join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in F)
        data=(head+'<vertices>\n'+vs+'\n    </vertices>\n    <triangles>\n'+ts+'\n    '+tail).encode()
    elif n=='3D/3dmodel.model':
        txt=data.decode()
        txt=re.sub(r'(<metadata name="ModificationDate">)[^<]*',r'\g<1>'+today,txt)
        txt=re.sub(r'(<metadata name="Description">)[^<]*',r'\g<1>back_cover_v2 (MakerWorld) with the battery bay reworked for the Meshnology standoff cage: 122 x 71 mm, 35 mm proud, guide rails, four snap latches, cyberpunk exterior detailing and a recess for an 85 x 53 mm copper name plate; fins and fan mount replaced by two 100 x 25 x 10 mm heat-sink pockets over an open window',txt)
        data=txt.encode()
    elif n=='Metadata/model_settings.config':
        txt=data.decode()
        txt=re.sub(r'face_count="\d+"',f'face_count="{len(F)}"',txt)
        txt=txt.replace('157.19999999999999 0 15.5','157.19999999999999 0 40')
        txt=txt.replace('value="back_cover_v2.stl"/>\n    <metadata key="extruder"','value="back_cover_v2 cage bay"/>\n    <metadata key="extruder"',1)
        data=txt.encode()
    elif n=='Metadata/project_settings.config':
        txt=data.decode()
        txt=txt.replace('"enable_support": "0"','"enable_support": "1"')
        txt=txt.replace('"support_on_build_plate_only": "0"','"support_on_build_plate_only": "1"')
        data=txt.encode()
    elif n in ('Metadata/plate_1.png','Metadata/plate_no_light_1.png'):
        data=render(512)
    elif n=='Metadata/plate_1_small.png':
        data=render(128)
    elif n=='Metadata/top_1.png':
        data=render(512,'top')
    zout.writestr(info,data)
zout.close()
z=zipfile.ZipFile(OUT); print(z.testzip(), len(z.namelist()))
