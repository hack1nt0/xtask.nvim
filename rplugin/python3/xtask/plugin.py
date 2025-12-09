import pynvim
from .utils import *
import pprint

log = logging.getLogger(__name__)

@pynvim.plugin
class Plugin(object):

    def __init__(self, nvim:pynvim.Nvim):
        self.nvim = nvim
        self._lastbufid = None
        self._term_winid = -1
        self._term_bufid = -1
        self._jobs_winid = -1

    @pynvim.function('TestFunction', sync=True)
    def testfunction(self, args):
        return 3

    @pynvim.command('TestCommand', nargs='*', range='')
    def testcommand(self, args, range):
        try:
            if self._term_winid == -1 or not self.nvim.api.win_is_valid(self._term_winid):
                if self._term_bufid == -1 or not self.nvim.api.buf_is_valid(self._term_bufid):
                    self._term_bufid = self.nvim.api.create_buf(False, True)
                self._term_winid = self.nvim.api.open_win(self._term_bufid, True, self.winopts(title='Terminal'))
                if self.nvim.api.get_option_value('buftype', {'buf': self._term_bufid}) != "terminal":
                    self.nvim.command('terminal')
            else:
                self.nvim.api.win_hide(self._term_winid)
        except Exception as e:
            self._debug('error', e)

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
    def current(self): return self.nvim.current.buffer.number
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

    @pynvim.command('XtaskGetChanId', nargs='*', range='')
    def XtaskGetChanId(self, args, range):
        self.nvim.out_write(str(self.nvim.channel_id) + '\n')

    @pynvim.function('xtaskgetchanid')
    def xtaskgetchanid(self, args):
        return self.nvim.channel_id

    def _respond(self, guid, method, *args):
        self.nvim.funcs.rpcnotify(guid, method, *args)
        # self.nvim.out_write(f'{pprint.pformat(args, indent=2)}\n')

    def _request(self, guid, method, *args):
        return self.nvim.funcs.rpcrequest(guid, method, *args)

    def _error(self, guid, *args):
        self.nvim.funcs.rpcnotify(guid, 'XtaskError', *args)
    
    def _debug(self, k, v):
        self.nvim.out_write(f'{k} = {pprint.pformat(v, indent=2)}\n')

    @pynvim.function('XtaskConf')
    def XtaskConf(self, args):
        global conf
        try:
            guid = int(args[0])
            # hostname = conf['hostname']
            # username = conf['username']
            # password = self._request('XtaskSync', hostname, username)
            # import requests
            newconf = self._request(guid, 'XtaskConf', conf)
            if newconf:
                conf.update(newconf) #TODO
                save_conf()
        except Exception as e:
            self._error(guid, e)

    # @pynvim.function('XtaskListFiles', sync=True)
    # def XtaskListFiles(self, args):
    #     try:
    #         guid = int(args[0])
    #         dirpath = args[1]
    #         self.nvim.command(f"lua require('telescope.builtin').find_files({dirpath})")
    #     except Exception as e:
    #         self._error(guid, e)

    @pynvim.function('XtaskListFilesAsync', sync=True)
    def XtaskListFilesAsync(self, args):
        try:
            guid, dirpath = args
            dirpath = os.path.expanduser(dirpath)
            cwd = os.getcwd()
            os.chdir(dirpath)
            files = []
            for filename in glob.iglob('**/*', recursive=True):
                if os.path.isdir(filename): continue
                st = os.stat(filename)
                files.append((filename, st.st_size, st.st_mode, st.st_ctime, st.st_mtime, st.st_atime))
            self._respond(guid, 'XtaskListFiles', files)
            os.chdir(cwd)
        except Exception as e:
            self._error(guid, e)

    @pynvim.function('XtaskListFiles', sync=True)
    def XtaskListFiles(self, args):
        try:
            dirpath = args[0]
            dirpath = os.path.expanduser(dirpath)
            cwd = os.getcwd()
            os.chdir(dirpath)
            files = []
            for filename in glob.iglob('**/*', recursive=True):
                if os.path.isdir(filename): continue
                st = os.stat(filename)
                files.append((filename, st.st_size, st.st_mode, st.st_ctime, st.st_mtime, st.st_atime))
            os.chdir(cwd)
            return '', files
        except Exception as e:
            return e, []

    @pynvim.function('XtaskGrepFiles', sync=True)
    def XtaskGrepFiles(self, args):
        try:
            guid = int(args[0])
            dirpath = args[1]
            self.nvim.command(f"lua require('telescope.builtin').live_grep({dirpath})")
        except Exception as e:
            self._error(guid, e)

    @pynvim.function('XtaskListHelpFiles', sync=True)
    def XtaskListHelpFiles(self, args):
        try:
            guid = int(args[0])
            dirpath = args[1]
            self.nvim.command("lua require('telescope.builtin').help_tags()")
        except Exception as e:
            self._error(guid, e)

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

    # @pynvim.function('XtaskList')
    # def XtaskList(self, args):
    #     try:
    #         guid = int(args[0])
    #         tasks = get_all_tasks()
    #         self._debug('tasks', tasks)
    #         dirpath = self._request(guid, 'XtaskList', tasks)
    #         self.nvim.chdir(dirpath)
    #         self.XtaskListFiles([guid, dirpath])
    #     except Exception as e:
    #         self._error(guid, e)

    @pynvim.function('XtaskListTasksAsync', sync=True)
    def XtaskListTasksAsync(self, args):
        try:
            guid, taskroot = args
            taskroot = os.path.expanduser(taskroot)
            if not os.path.exists(taskroot):
                self._error(guid, f'[{taskroot}] not exists..')
                return
            if not os.path.isdir(taskroot):
                self._error(guid, f'[{taskroot}] exists, but is not a directory..')
                return
            tasks = get_all_tasks(taskroot)
            self._debug('tasks', tasks)
            self._respond(guid, 'XtaskListTasks', tasks)
        except Exception as e:
            self._error(guid, e)

    @pynvim.function('XtaskListTasks', sync=True)
    def XtaskListTasks(self, args):
        try:
            taskhome = args[0]
            taskhome = os.path.expanduser(taskhome)
            if not os.path.exists(taskhome):
                return f'[{taskhome}] not exists..', []
            if not os.path.isdir(taskhome):
                return f'[{taskhome}] exists, but is not a directory..', []
            tasks = get_all_tasks(taskhome)
            self._debug('tasks', tasks)
            return '', tasks
        except Exception as e:
            return e, []

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
                needupd = newxinfo != oldxinfo
                if needupd: 
                    update_xinfo(self.cwd)
                    self._respond(guid, 'XtaskEdit', needupd)
                else:
                    self._error(guid, 'Nothing changed..')
            else:
                self._error(guid, 'Current directory is not a xtask..')
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
    
    # def _checkterm(self, bufid):
    #     # self.nvim.funcs.bo[bufid].buftype == "terminal":
    
    # def _getchannel(self, bufid):
    #     # self.nvim.funcs.bo[bufid].buftype == "terminal":

    def winopts(self, title='', footer=''):
        rows = int(self.nvim.options.get('lines', '20'))
        cols = int(self.nvim.options.get('columns', '30'))
        global conf
        p = conf['termw%']
        w = int(cols * p)
        h = rows - 4
        x = cols - w
        y = 0
        return {
            'relative': 'editor',
            'width': w,
            'height': h,
            'col': x,
            'row': y,
            # 'style': 'minimal',
            'border': [ "╔", "═" ,"╗", "║", "╝", "═", "╚", "║" ],
            'title': title,
            'title_pos': 'center',
            'footer': footer,
            'footer_pos': 'center',
        }

    @pynvim.function('XtaskToggleTerm')
    def XtaskToggleTerm(self, args):
        try:
            guid = int(args[0])
            on = len(args) < 2 or args[1]
            if not self.nvim.api.win_is_valid(self._term_winid):
                if not self.nvim.api.buf_is_valid(self._term_bufid):
                    self._term_bufid = self.nvim.api.create_buf(False, True)
                    if self.nvim.api.get_option_value('buftype', {'buf': self._term_bufid}) != "terminal":
                        self.nvim.command('terminal')
                self._term_winid = self.nvim.api.open_win(self._term_bufid, True, self.winopts(title='Terminal'))
            elif not on:
                self.nvim.api.win_hide(self._term_winid)
        except Exception as e:
            self._error(guid, e)

    @pynvim.function('XtaskRunCmd')
    def XtaskRunCmd(self, args):
        try:
            self._debug('XtaskRunCmd', args)
            guid = int(args[0])
            cmd = ' && '.join(args[1:])
            self.XtaskToggleTerm([guid, True])
            chanid = self.nvim.api.get_option_value('channel', {'buf': self._term_bufid})
            def cc():
                return self.nvim.api.get_proc_children(self.nvim.call('jobpid', chanid))
            if not cc():
                self.nvim.api.chan_send(chanid, f'{cmd}\n') #Send a command and newline to execute it
            else:
                self._error(guid, "Terminal is busy..\nUse `Job` instead")
        except Exception as e:
            self._error(guid, e)
    
    @pynvim.function('XtaskRunJob')
    def XtaskRunJob(self, args):
        try:
            guid = int(args[0])
            cmd = ' && '.join(args[1:])
            if self.nvim.api.win_is_valid(self._jobs_winid):
                self.nvim.api.hide_win(self._jobs_winid)
            bufid = self.nvim.api.create_buf(False, True)
            self.nvim.command(f'terminal {cmd}')
            self._jobs_winid = self.nvim.api.open_win(bufid, True, self.winopts(title=f'Job #{bufid}', footer=f'[{cmd}]'))
        except Exception as e:
            self._error(guid, e)
        
    @pynvim.function('XtaskListJobs')
    def XtaskListJobs(self, args):
        try:
            guid = int(args[0])
            bufid, cmd = self._request(guid, 'XtaskListJobs', self.nvim.command_output('ls'))
            if bufid is not None:
                if self.nvim.api.win_is_valid(self._jobs_winid):
                    self.nvim.api.hide_win(self._jobs_winid)
                self._jobs_winid = self.nvim.api.open_win(bufid, True, self.winopts(title=f'Job #{bufid}', footer=f'[{cmd}]'))
        except Exception as e:
            self._error(guid, e)


    @pynvim.function('XtaskSync')
    def XtaskSync(self, args):
        global conf
        try:
            guid = int(args[0])
            # hostname = conf['hostname']
            # username = conf['username']
            # password = self._request('XtaskSync', hostname, username)
            # import requests
            gitrepo = conf['gitrepo']
            gitbranch = conf['gitrepo']
            self.XtaskRunJob([guid, f'git remote set-url origin {gitrepo}', f'git push origin {gitbranch}'])
        except Exception as e:
            self._error(guid, e)
        