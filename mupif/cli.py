import typer
try: from rich import print
except ImportError: pass

app=typer.Typer()

@app.command()
def vpn():
    import mupif.monitor
    print(mupif.monitor.vpnInfo())

@app.command()
def version():
    import mupif.util
    print(mupif.util.getVersion()._asdict())

@app.command()
def jobmans():
    import mupif.monitor, mupif.pyroutil
    print(mupif.monitor.jobmanInfo(ns=mupif.pyroutil.connectNameserver()))

@app.command()
def schedulers():
    import mupif.monitor, mupif.pyroutil
    print(mupif.monitor.schedulerInfo(ns=mupif.pyroutil.connectNameserver()))

@app.command()
def schedmon():
    import mupif as mp
    import mupif.pyroutil
    import mupif.monitor
    import time, datetime
    import rich.live, rich.console, rich.text, rich.tree

    def exeStatusStyle(stat):
        return {'processed':'blue','scheduled':'cyan','running':'yellow','finished':'green','failed':'red'}[stat.lower()]

    with rich.live.Live(console=rich.console.Console(markup=True),refresh_per_second=2) as live:
        ns=mp.pyroutil.connectNameserver()
        while True:
            ssi=mp.monitor.schedulerInfo(ns)
            tree=rich.tree.Tree(f'Schedulers at {datetime.datetime.now().isoformat(timespec="seconds",sep=" ")}')
            for si in ssi:
                tree2=tree.add(f'{si["ns"]["name"]} at {si["ns"]["uri"]}')
                nt=si['numTasks']
                tree2.add(rich.text.Text.from_markup(', '.join([f'{st}: [{exeStatusStyle(st)}]{nt[st]}[/]' for st in ('processed','scheduled','running','finished','failed')])))
                tab=rich.table.Table('WEid','Wid','status','start/finish')
                for lex in si['lastExecutions']:
                    tab.add_row(lex['weid'],lex['wid'],rich.text.Text(lex['status'],style=exeStatusStyle(lex['status'])),lex['finished'] if lex['finished'] is not None else lex['started'])
                tree2.add(tab)
                for weid,rr in si['running'].items():
                    ex=tree2.add(weid)
                    import rich.logging
                    handler=rich.logging.RichHandler()
                    for l in rr['tail']:
                        ex.add(handler.render(record=l,traceback=None,message_renderable=rich.text.Text(l.message)))
            live.update(tree)
            time.sleep(.5)

#
# ns subcommands
#
app.add_typer(ns_app:=typer.Typer(),name='ns',)
# call "ns list" if only "ns" is given
@ns_app.callback(invoke_without_command=True)
@ns_app.command()
def list():
    import mupif.monitor
    print(mupif.monitor.nsInfo())

def main():
    import sys
    if len(sys.argv)==1: sys.argv.append('--help')
    app()

if __name__ == '__main__':
    main()

