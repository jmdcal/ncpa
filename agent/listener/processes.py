import psutil
import logging
import nodes


class ProcessNode(nodes.LazyNode):

    def get_exe(self, request_args):
        return request_args.get('exe', [])

    def get_name(self, request_args):
        return request_args.get('name', [])

    def get_count(self, request_args):
        count = request_args.get('count', 0)
        if count:
            count = count[0]
        return count

    def get_cpu_percent(self, request_args):
        cpu_percent = request_args.get('cpu_percent', None)
        if cpu_percent:
            cpu_percent = cpu_percent[0]
        return cpu_percent

    def get_mem_percent(self, request_args):
        mem_percent = request_args.get('mem_percent', None)
        if mem_percent:
            mem_percent = mem_percent[0]
        return mem_percent

    def get_combiner(self, request_args):
        combiner = request_args.get('combiner', 'and')
        if combiner == 'and':
            return all
        else:
            return any

    def make_filter(self, *args, **kwargs):
        exes = self.get_exe(kwargs)
        names = self.get_name(kwargs)
        cpu_percent = self.get_cpu_percent(kwargs)
        mem_percent = self.get_mem_percent(kwargs)
        comparison = self.get_combiner(kwargs)

        def proc_filter(process):
            comp = []
            for exe in exes:
                comp.append(process.exe() in exe)
            for name in names:
                comp.append(process.name() in name)
            if not cpu_percent is None:
                comp.append(cpu_percent < process.cpu_percent())
            if not cpu_percent is None:
                comp.append(mem_percent < process.memory_percent())
            return comparison(comp)

        return proc_filter

    @staticmethod
    def standard_form(process):
        return {'name:': process.name(),
                'exe:': process.exe(),
                'cpu_percent': process.cpu_percent(),
                'mem_percent': process.memory_percent()}

    def get_process_dict(self, *args, **kwargs):
        proc_filter = self.make_filter(*args, **kwargs)
        processes = []

        for process in psutil.process_iter():
            if proc_filter(process):
                process_json = self.standard_form(process)
                processes.append(process_json)

        return processes

    def walk(self, *args, **kwargs):
        self.method = self.get_process_dict
        if kwargs.get('first', True):
            logging.error('Doing the method')
            return {self.name: self.method(*args, **kwargs)}
        else:
            return {self.name: []}

    def get_process_label(self, request_args):
        title = 'Process count'

        exes = self.get_exe(request_args)
        names = self.get_name(request_args)
        cpu_percent = self.get_cpu_percent(request_args)
        mem_percent = self.get_mem_percent(request_args)

        if self.get_combiner(request_args) == all:
            combiner = 'and'
        else:
            combiner = 'or'

        if exes or names or cpu_percent or mem_percent:
            title += ' for'
            if exes:
                title += ' exes named '
                title += ','.join(exes)
                if names or cpu_percent or mem_percent:
                    title += ' ' + combiner
            if names:
                title += ' processes named '
                title += ','.join(names)
                if cpu_percent or mem_percent:
                    title += ' ' + combiner
            if cpu_percent:
                title += ' CPU usage greater than %d%%' % cpu_percent
                if mem_percent:
                    title += ' ' + combiner
            if mem_percent:
                title += ' Memory Usage greater than %d%%' % mem_percent
        logging.error(title)
        return [title]

    def run_check(self, *args, **kwargs):

        def process_check_method(*args, **kwargs):
            processes_count = self.walk(first=True, *args, **kwargs)
            count = len(processes_count['process'])
            return [count, 'c']

        self.method = process_check_method

        if kwargs.get('perfdata_label', None) is None:
            kwargs['perfdata_label'] = ['process_count']

        if kwargs.get('title', None) is None:
            kwargs['title'] = self.get_process_label(kwargs)
            logging.error('Set new title!')

        return super(ProcessNode, self).run_check(*args, **kwargs)