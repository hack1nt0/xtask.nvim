import pynvim
from .utils import *
import pprint

log = logging.getLogger(__name__)

@pynvim.plugin
class Plugin(object):

    def __init__(self, nvim:pynvim.Nvim):
        self.nvim = nvim
        self._lastbufid = None

    @pynvim.function('TestFunction', sync=True)
    def testfunction(self, args):
        return 3

    @pynvim.command('TestCommand', nargs='*', range='')
    def testcommand(self, args, range):
        self.nvim.current.line = ('Command with args: {}, range: {}'
                                  .format(args, range))

    @pynvim.autocmd('BufEnter', pattern='*.py', eval='expand("<afile>")', sync=True)
    def on_bufenter(self, filename):
        self.nvim.out_write('testplugin is in ' + filename + '\n')

    @property
    def cwd(self) -> str: 
        # return os.path.dirname(os.path.expanduser(self.nvim.current.buffer.name))
        return self.nvim.command_output('pwd')

    @property
    def headless(self) -> bool: return self.guid is not None

    @property
    def guid(self):
        chans = self.nvim.api.list_chans()
        self._debug('chans', chans)
        res = None
        for chan in chans:
            if 'client' in chan and chan['client'].get('name', None) == 'python3-client' and \
                chan['client'].get('type', None) == 'remote':
                res = chan['id']
                break
        self._debug('res', res)
        return res

    def _respond(self, guid, method, *args):
        self.nvim.funcs.rpcnotify(guid, method, *args)
        # self.nvim.out_write(f'{pprint.pformat(args, indent=2)}\n')

    def _request(self, guid, method, *args):
        return self.nvim.funcs.rpcrequest(guid, method, *args)

    def _error(self, guid, *args):
        self.nvim.funcs.rpcnotify(guid, 'XtaskError', *args)
    
    def _debug(self, k, v):
        self.nvim.out_write(f'{k} = {pprint.pformat(v, indent=2)}\n')


    @pynvim.function('XtaskNew', sync=True)
    def XtaskNew(self, args):
        try:
            self._debug('xinfo', args)
            guid, xinfo = args
            # guid = int(args[0])
            # jsonstr = ' '.join(args[1:])
            # xinfo = json.loads(jsonstr)
            xname = xinfo.get('name', None)
            if not xinfo or not xname:
                self._error(guid, f'Invalid xinfo:\n{xinfo}')
                return
            src = template_dir
            dst = os.path.join(task_dir, taskname_to_dirname(xname))
            if os.path.exists(dst):
                self._error(guid, f'[{xname}] already exists as folder {dst}')
                return
            shutil.copytree(src, dst)
            tcs = xinfo.get('tests', [{"input": "", "output": ""}])
            for i, tc in enumerate(tcs, start=1): 
                with open(os.path.join(dst, f'{i}.tc'), 'w') as w: 
                    w.write(tc['input'])
                    w.write('\n')
                    w.write(tc['output'])
            xinfo['tcs'] = "*.tc"
            xinfo['ctime'] = str(time.time_ns())
            fname = os.path.join(dst, 'xtask.json')
            open(fname, 'w').write(json.dumps(xinfo, indent=4))
            update_xinfo(dst)
            self._respond(guid, 'XtaskNew', xname, dst)
        except Exception as e:
            self._error(guid, e)

    @pynvim.function('XtaskList')
    def XtaskList(self, args):
        try:
            guid = int(args[0])
            tasks = get_all_tasks()
            self._debug('tasks', tasks)
            self._respond(guid, 'XtaskList', tasks)
        except Exception as e:
            self._error(guid, e)

    # @pynvim.command('XtaskRequestInfo', nargs=1)
    # def XtaskRequestInfo(self):
    #     pass

    @pynvim.function('XtaskEdit')
    def XtaskEdit(self, args):
        try:
            guid = int(args[0])
            fname = os.path.join(self.cwd, 'xtask.json')
            if os.path.exists(fname):
                oldxinfo = open(fname).read()
                newxinfo = self._request(guid, 'XtaskEdit', oldxinfo)
                if newxinfo is None: return
                if newxinfo != oldxinfo: update_xinfo(self.cwd)
                self._respond(guid, 'XtaskEdit')
            else:
                self._error(guid, 'Current directory is not a xtask..')
        except Exception as e:
            self._error(guid, e)

    @pynvim.function('XtaskSpecify')
    def XtaskSpecify(self, args):
        try:
            guid = int(args[0])
            dirpath = args[1]
            self.nvim.chdir(dirpath)
        except Exception as e:
            self._error(guid, e)

    @pynvim.function('XtaskDel')
    def XtaskDel(self, args):
        try:
            guid = int(args[0])
            delete_task(self.cwd)
            self.nvim.chdir(task_dir)
            self.XtaskList([guid])
        except Exception as e:
            self._error(guid, e)
    
    # def XtaskReceiveInfo(self, xinfo):
    #     pass

    @pynvim.function('XtaskRun')
    def XtaskRun(self, args):
        try:
            guid = int(args[0])
            info = get_xinfo(self.cwd)
            # script = os.path.join(USERHOME, 'xvim', 'py')
            script = os.path.join(os.path.dirname(__file__), 'utils.py')
            test_cmd = f'python3 {script} {self.cwd}'
            compile_cmd = 'make all'
            # 0scr.command(f'terminal {compile_cmd} && {test_cmd}')
            cmd = f'{compile_cmd} && {test_cmd}'
            self.XtaskCmd(cmd) 
        except Exception as e:
            self._error(guid, e)
    
    @pynvim.function('XtaskCopy')
    def XtaskCopy(self, args):
        try:
            guid = int(args[0])
            xinfo = get_xinfo(self.cwd)
            solfile= xinfo['sol']
            if not os.path.exists(solfile):
                self._error(f'\n{solfile} not exists..')
                return
            if os.path.splitext(xinfo['sol'])[-1] == '.cpp':
                from .cppzip import run
                outfile = f'{solfile}.zip'
                with open(outfile, 'w+') as w: 
                    err = run(solfile, w)
                    if err:
                        self._error(f'{err}')
                        return
                msg = f'CppZip\n{solfile} has been zip to {outfile}'
            else:
                msg = f'\nNo Zipper found for {solfile}'
                outfile = solfile
            content = open(outfile).read()
            self._respond('XtaskCopy', msg, content)
        except Exception as e:
            self._error(guid, e)
    
    @property
    def terminal(self):
        while True:
            bufs = self.nvim.buffers
            for buf in bufs:
                if self._checkterm(buf.number):
                    return buf.number
            self.nvim.command('terminal')

    @property
    def current(self): return self.nvim.current.buffer.number

    def _checkterm(self, bufid):
        # self.nvim.funcs.bo[bufid].buftype == "terminal":
        return self.nvim.api.get_option_value('buftype', {'buf': bufid}) == "terminal"
    
    def _getchannel(self, bufid):
        # self.nvim.funcs.bo[bufid].buftype == "terminal":
        return self.nvim.api.get_option_value('channel', {'buf': bufid})

    @pynvim.function('XtaskSwitch')
    def XtaskSwitch(self, args):
        try:
            guid = int(args[0])
            termid = self.terminal
            if self.current != termid:
                self._lastbufid = self.current
                self.nvim.command(f'b {termid}')
            else:
                if self._lastbufid is None or self._lastbufid == termid:
                    self.nvim.command(f'bfirst')
                else:
                    self.nvim.command(f'b {self._lastbufid}')
        except Exception as e:
            self._error(guid, e)

    @pynvim.function('XtaskCmd')
    def XtaskCmd(self, args):
        try:
            self._debug('cmd', args)
            guid = int(args[0])
            cmd = ' '.join(args[1:])
            termid = self.terminal
            self.nvim.command(f'b {termid}')
            chanid = self._getchannel(termid)
            def cc():
                return self.nvim.api.get_proc_children(self.nvim.call('jobpid', chanid))
            if not cc():
                self.nvim.api.chan_send(chanid, f'{cmd}\n') #Send a command and newline to execute it
                tic = time.time_ns()
                while True:
                    time.sleep(0.1)
                    if not cc():
                        toc = time.time_ns()
                        tot = round((toc - tic) / 1e9, 2)
                        self._respond(guid, 'XtaskCmd', cmd, 'finished in {tot} seconds')
            else:
                self._error(guid, "A job is running\nUse `task` instead..")
        except Exception as e:
            self._error(guid, e)
    
    @pynvim.function('XtaskTask')
    def XtaskTask(self, args):
        try:
            self._debug('task', args)
            guid = int(args[0])
            cmd = ' && '.join(args[1:])
            self.nvim.command(f'terminal {cmd}')
        except Exception as e:
            self._error(guid, e)
        

    @pynvim.function('XtaskSync')
    def XtaskSync(self, args):
        try:
            self._debug('task', args)
            guid = int(args[0])
            # hostname = conf['hostname']
            # username = conf['username']
            # password = self._request('XtaskSync', hostname, username)
            # import requests
            gitrepo = conf['gitrepo']
            gitrepo = self._request('XtaskSync', gitrepo)
            self.XtaskTask([guid, f'git remote set-url origin {gitrepo}', 'git push'])
            self.nvim.command_(f'terminal {cmd}')
        except Exception as e:
            self._error(guid, e)
        