import runpy,sys
from pathlib import Path
p=Path(sys.argv[1]);sys.path.insert(0,str(p.parent));sys.argv=[str(p)]
def guard(event,args):
 if event in ('socket.connect','socket.bind'):raise RuntimeError('network forbidden')
 if event=='open' and isinstance(args[0],(str,bytes)) and any(v in str(args[0]).lower() for v in ('.env','.session','.pem')):raise RuntimeError('credential read forbidden')
sys.addaudithook(guard)
runpy.run_path(str(p),run_name='__main__')
