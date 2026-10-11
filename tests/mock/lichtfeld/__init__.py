"""Mock di lichtfeld per i test offline (comportamenti ricavati dalla sorgente 0.5.5)."""
import math, types
import numpy as np

class _Log:
    def __init__(self): self.lines=[]
    def info(self,m): self.lines.append(("I",m))
    def warn(self,m): self.lines.append(("W",m))
    def error(self,m): self.lines.append(("E",m))
    def debug(self,m): pass
log=_Log()
PLUGIN_API_VERSION="1.0"

def _nrm(v): v=np.asarray(v,float); return v/np.linalg.norm(v)
class CameraState:
    def __init__(s,eye,target,up,fov=60.0): s.eye,s.target,s.up,s.fov=tuple(eye),tuple(target),tuple(up),fov
_cam=CameraState((0,0,10),(0,0,0),(0,1,0))
def get_camera(panel='main'): return _cam
def set_camera(eye,target,up=(0,1,0),panel='main'):
    """Come visualizer_impl: ortogonalizza l'up; get_camera restituisce l'up della camera."""
    global _cam
    e,t=np.array(eye,float),np.array(target,float); f=_nrm(t-e)
    r=np.cross(f,up)
    if np.linalg.norm(r)<1e-6: return  # degenere: ignorato con warning
    r=_nrm(r); u=np.cross(r,f)
    _cam=CameraState(eye,target,tuple(u),_cam.fov)
_ortho=[False]; _oscale=[50.0]
def set_orthographic(o,extent_world=None):
    if extent_world is not None and not o: raise ValueError("extent requires ortho")
    _ortho[0]=o
    if extent_world: _oscale[0]=900.0/extent_world
def is_orthographic(): return _ortho[0]
class ViewInfo:
    def __init__(s): s.width=1600; s.height=900; s.orthographic=_ortho[0]; s.ortho_scale=_oscale[0]
def get_current_view(panel='main'): return ViewInfo()

_handlers={}
def add_draw_handler(i,cb,timing='POST_VIEW'): _handlers[i]=cb
def remove_draw_handler(i): return _handlers.pop(i,None) is not None
def has_draw_handler(i): return i in _handlers

_registered=[]
def register_class(c): _registered.append(c)
def unregister_class(c): _registered.remove(c)

class _T:
    def __init__(s,a): s.a=np.asarray(a)
    def cpu(s): return s
    def numpy(s): return s.a
    def __getitem__(s,k): return _T(s.a[k])
class SplatData:
    def __init__(s,pts): s._p=pts; s.num_points=len(pts)
    def get_means(s): return _T(s._p)
class Node:
    def __init__(s,pts,M=None):
        s._sd=SplatData(pts); s.world_transform=tuple(np.ravel(M if M is not None else np.eye(4)))
    def splat_data(s): return s._sd
    def point_cloud(s): return None
class Scene:
    def __init__(s,pts,M=None): s._n=[Node(pts,M)]; s._m=SplatData(pts); s.total_gaussian_count=len(pts)
    def combined_model(s): return s._m
    def get_nodes(s,t=None): return s._n
_scene=[None]
def get_scene(): return _scene[0]

class _RS:
    def __init__(s): s.p={'show_grid':True,'grid_plane':'1','grid_opacity':0.5}
    def get_all_properties(s): return dict(s.p)
    def get(s,k): return s.p[k]
    def set(s,k,v):
        if k not in s.p: raise KeyError(k)
        s.p[k]=v
_rs=_RS()
def get_render_settings(): return _rs

class _Ops:
    def get_all(s): return ['zup_view.zup_ops.ZupOrbitOperator']
ops=_Ops()

class _Ret:
    running_modal=True; finished=False; status="RUNNING_MODAL"
    def __bool__(s): return False
class _UiOps:
    invoked=[]; modal=[False]
    def invoke(s,i,**k):
        if i not in [c._class_id() for c in _registered if hasattr(c,'_class_id')]:
            raise RuntimeError("Operator not found "+i)
        s.invoked.append(i); s.modal[0]=True; return _Ret()
    def cancel_modal(s): raise AssertionError("cancel_modal globale non deve essere usato")
    def has_modal(s): return s.modal[0]
class PanelSpace: MAIN_PANEL_TAB=0
class Panel: pass
_lang=["it"]; _redraws=[0]
def _req(delay=0.0): _redraws[0]+=1
ui=types.SimpleNamespace(Panel=Panel,PanelSpace=PanelSpace,ops=_UiOps(),get_current_language=lambda: _lang[0],request_redraw=_req)

class _Settings:
    store={}
    def __init__(s,name): s.d=_Settings.store.setdefault(name,{})
    def all(s): return dict(s.d)
    def update(s,v): s.d.update(v)
import tempfile, os
_DATA=tempfile.mkdtemp(prefix="lfsdata")
def _data_dir(n):
    d=os.path.join(_DATA,n); os.makedirs(d,exist_ok=True); return d
plugins=types.SimpleNamespace(settings=lambda n: _Settings(n), data_dir=_data_dir)
