"""Pseudo-builders for building and registering benchmarks.
"""
import os
from SCons.Script import Action

def exists(env):
    return True

_benchmarks = []
def register_benchmark(env, test):
    _benchmarks.append(test.path)
    env.Alias('$BENCHMARK_ALIAS', test)

def benchmark_list_builder_action(env, target, source):
    ofile = open(str(target[0]), 'w')
    try:
        for s in _benchmarks:
            print('\t' + str(s))
            ofile.write('%s\n' % s)
    finally:
        ofile.close()

def build_benchmark(env, target, source, **kwargs):

    bmEnv = env.Clone()
    bmEnv.InjectThirdParty(libraries=['benchmark'])

    if bmEnv.TargetOSIs('windows'):
        bmEnv.Append(LIBS=["ShLwApi.lib"])

    libdeps = kwargs.get('LIBDEPS', [])
    libdeps.append('$BUILD_DIR/mongo/unittest/benchmark_main')

    kwargs['LIBDEPS'] = libdeps
    kwargs['INSTALL_ALIAS'] = ['benchmarks']

    result = bmEnv.Program(target, source, **kwargs)
    bmEnv.RegisterBenchmark(result[0])
    hygienic = bmEnv.GetOption('install-mode') == 'hygienic'
    if not hygienic:
        installed_test = bmEnv.Install("#/build/benchmark/", result[0])
        env.Command(
            target="#@{}".format(os.path.basename(installed_test[0].path)),
            source=installed_test,
            action="${SOURCES[0]}"
        )
    else:
        test_bin_name = os.path.basename(result[0].path)
        env.Command(
            target="#@{}".format(test_bin_name),
            source=["$PREFIX_BINDIR/{}".format(test_bin_name)],
            action="${SOURCES[0]}"
        )

    return result


def generate(env):
    env.Command('$BENCHMARK_LIST', env.Value(_benchmarks),
                Action(benchmark_list_builder_action, "Generating $TARGET"))
    env.AddMethod(register_benchmark, 'RegisterBenchmark')
    env.AddMethod(build_benchmark, 'Benchmark')
    env.Alias('$BENCHMARK_ALIAS', '$BENCHMARK_LIST')
