from .Client import *
from .Job import *
import base64
from IPython.display import Javascript

class CyberGISCompute:
    # static variable
    jupyterhubApiToken = None

    def __init__(self, url="cgjobsup.cigi.illinois.edu", port=443, isJupyter=True, protocol='HTTPS'):
        self.client = Client(url, port, protocol)
        self.jupyterhub_api_token = None
        self.isJupyter = isJupyter
        if isJupyter:
            self.enable_jupyter()

    def login(self, host=None):
        if path.exists('./cybergis_compute_user.json'):
            with open(os.path.abspath('cybergis_compute_user.json')) as f:
                user = json.load(f)
                token = user['token']
                print('📃 found "cybergis_compute_user.json"')
                try:
                    res = self.client.request('GET', '/user', { "jupyterhubApiToken": token })
                    print('✅ successfully logged in as ' + res['username'])
                    self.jupyterhub_api_token = token
                except:
                    print('❌ invalid Jupyter token')
                print('NOTE: if you want to login as another user, please remove this file')
        else:
            if self.isJupyter:
                if (self.jupyterhubApiToken != None):
                    import getpass
                    print('📢 please go to Control Panel -> Token, request a new API token')
                    token = getpass.getpass('enter your API token here')
                    token = base64.b64encode((self.jupyterhubApiToken + '@' + token).encode('ascii')).decode('utf-8')
                    try:
                        res = self.client.request('GET', '/user', { "jupyterhubApiToken": token })
                        print('✅ successfully logged in as ' + res['username'])
                        self.jupyterhub_api_token = token
                        with open('./cybergis_compute_user.json', 'w') as json_file:
                            json.dump({ "token": token }, json_file)
                    except:
                        print('❌ invalid Jupyter token')
                else:
                    print('❌ you might not be working on a web browser or enabled JavaScript')
            else:
                print('❌ enable Jupyter using .enable_jupyter() before you login')

    def create_job(self, maintainer='community_contribution', hpc=None, username=None, password=None):
        return Job(maintainer, hpc, None, username, password, self.client, isJupyter=self.isJupyter, jupyterhubApiToken=self.jupyterhubApiToken)

    def get_job_by_id(self, id=None):
        jobs = self.client.request('GET', '/user/job', { "jupyterhubApiToken": self.jupyterhub_api_token })
        token = None
        for i in jobs['job']:
            job = jobs['job'][i]
            if (job['id'] == id):
                token = job['secretToken']
        if (token == None):
            print('❌ job with id ' + id + ' was not found')
        return Job(secretToken=token, isJupyter=self.isJupyter, jupyterhubApiToken=self.jupyterhubApiToken)

    def list_job(self):
        if self.jupyterhub_api_token == None:
            print('❌ please login frist using .login()')

        jobs = self.client.request('GET', '/user/job', { "jupyterhubApiToken": self.jupyterhub_api_token })

        headers = ['id', 'maintainer', 'hpc', 'executableFolder', 'dataFolder', 'resultFolder', 'param', 'slurm', 'createdAt']
        data = []
        for i in jobs['job']:
            job = jobs['job'][i]
            data.append([
                job['id'],
                job['maintainer'],
                job['hpc'],
                job['executableFolder'],
                job['dataFolder'],
                job['resultFolder'],
                json.dumps(job['param']),
                json.dumps(job['slurm']),
                job['createdAt'],
            ])

        if self.isJupyter:
            display(HTML(tabulate(data, headers, numalign='left', stralign='left', colalign=('left', 'left'), tablefmt='html').replace('<td>', '<td style="text-align:left">').replace('<th>', '<th style="text-align:left">')))
        else:
            print(tabulate(data, headers, tablefmt="presto"))

    def list_hpc(self):
        hpc = self.client.request('GET', '/hpc')['hpc']
        headers = ['hpc', 'ip', 'port', 'is_community_account']
        data = []

        for i in hpc:
            data.append([
                i,
                hpc[i]['ip'],
                hpc[i]['port'],
                hpc[i]['is_community_account']
            ])

        if self.isJupyter:
            if len(data) == 0:
                print('empty')
                return
            display(HTML(tabulate(data, headers, numalign='left', stralign='left', colalign=('left', 'left'), tablefmt='html').replace('<td>', '<td style="text-align:left">').replace('<th>', '<th style="text-align:left">')))
        else:
            print(tabulate(data, headers, tablefmt="presto"))

    def list_container(self):
        hpc = self.client.request('GET', '/container')['container']
        headers = ['container name', 'dockerfile', 'dockerhub']
        data = []

        for i in hpc:
            data.append([
                i,
                hpc[i]['dockerfile'],
                hpc[i]['dockerhub']
            ])

        if self.isJupyter:
            if len(data) == 0:
                print('empty')
                return
            display(HTML(tabulate(data, headers, numalign='left', stralign='left', colalign=('left', 'left'), tablefmt='html').replace('<td>', '<td style="text-align:left">').replace('<th>', '<th style="text-align:left">')))
        else:
            print(tabulate(data, headers, tablefmt="presto"))

    def list_git(self):
        git = self.client.request('GET', '/git')['git']
        headers = ['link', 'name', 'container', 'repository', 'commit']
        data = []

        for i in git:
            data.append([
                'git://' + i,
                git[i]['name'],
                git[i]['container'],
                git[i]['repository'],
                git[i]['commit'] if 'commit' in git[i] else 'NONE' ,
            ])

        if self.isJupyter:
            if len(data) == 0:
                print('empty')
                return
            display(HTML(tabulate(data, headers, numalign='left', stralign='left', colalign=('left', 'left'), tablefmt='html').replace('<td>', '<td style="text-align:left">').replace('<th>', '<th style="text-align:left">')))
        else:
            print(tabulate(data, headers, tablefmt="presto"))

    def list_maintainer(self):
        maintainers = self.client.request('GET', '/maintainer')['maintainer']
        headers = ['maintainer', 'hpc', 'default_hpc', 'job_pool_capacity', 'executable_folder->from_user', 'executable_folder->must_have']
        data = []

        for i in maintainers:
            maintainer = maintainers[i]

            from_user = 'not specified'
            if 'executable_folder' in maintainer:
                from_user = maintainer['executable_folder']['from_user']

            must_have = 'not specified'
            if 'executable_folder' in maintainer:
                if 'file_config' in maintainer['executable_folder']:
                    if 'must_have' in maintainer['executable_folder']['file_config']:
                        must_have = maintainer['executable_folder']['file_config']['must_have']

            data.append([
                i,
                maintainer['hpc'],
                maintainer['default_hpc'],
                maintainer['job_pool_capacity'],
                from_user,
                must_have
            ])
        
        if self.isJupyter:
            if len(data) == 0:
                print('empty')
                return
            display(HTML(tabulate(data, headers, numalign='left', stralign='left', colalign=('left', 'left'), tablefmt='html').replace('<td>', '<td style="text-align:left">').replace('<th>', '<th style="text-align:left">')))
        else:
            print(tabulate(data, headers, tablefmt="presto"))


    def enable_jupyter(self):
        self.isJupyter = True
        # get jupyter variable
        display(Javascript('IPython.notebook.kernel.execute(`CyberGISCompute.jupyterhubApiToken = "${window.location.host}"`);'))