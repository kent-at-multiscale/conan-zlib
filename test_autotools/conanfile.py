import os

import conans


class AutotoolsZlibUser(conans.ConanFile):
    """
    This tests the zlib package by building an application that links to it.
    This uses Autoconf and Automake to build.
    """
    settings = 'os', 'compiler', 'build_type', 'arch'
    exports_sources = 'Makefile.am', 'configure.ac', 'src/Makefile.am', 'src/main.cpp', 'm4/*'
    requires = 'zlib/1.2.11@kent_at_multiscale/stable'
    generators = 'env', 'txt'
    
    def system_requirements(self):
        if self.scope.installTools:
            try:
                installer = conans.tools.SystemPackageTool()
                installer.update()
                installer.install('autoconf')
                installer.install('automake')
                installer.install('libtool')
                installer.install('make')
                installer.install('pkg-config')
            except:
                self.output.warn('Unable to bootstrap required build tools.  If they are already installed, you can ignore this warning.')
    
    def imports(self):
        self.copy(pattern='*', dst='bin', src='bin')
        if conans.tools.os_info.is_windows:
            self.copy(pattern='*.dll', dst='bin', src='bin')
        elif conans.tools.os_info.is_macos:
            self.copy(pattern='*.dylib', dst='lib', src='lib')
        else:
            self.copy(pattern='*.so.*', dst='lib', src='lib')
            self.copy(pattern='*.so', dst='lib', src='lib')
    
    def build(self):
        # Trick conan: .conanfile_directory
        build_env = conans.AutoToolsBuildEnvironment(self)
        build_env.fpic = True
        
        # The autotools tool is setting the same info we get from pkg-config
        # Therefore, we can clear out these variables.
        build_env.libs = []
        build_env.include_paths = []
        build_env.library_paths = []
        
        self.output.info('build defines: %s' % (build_env.defines))
        self.output.info('build flags: %s' % (build_env.flags))
        self.output.info('build cxx_flags: %s' % (build_env.cxx_flags))
        self.output.info('build include_paths: %s' % (build_env.include_paths))
        self.output.info('build libs: %s' % (build_env.libs))
        self.output.info('build library_paths: %s' % (build_env.library_paths))
        self.output.info('build link_flags: %s' % (build_env.link_flags))
        
        rpath = []
        if conans.tools.os_info.is_macos:
            rpath.append('@executable_path/../lib')
        elif conans.tools.os_info.is_windows:
            pass
        else:
            rpath.append('\\$$ORIGIN/../lib')
        
        for p in rpath:
            build_env.link_flags.append('-Wl,-rpath,%s' % (p))
        
        self.output.info('rpath: %s' % (' '.join('-Wl,-rpath,%s' % p for p in rpath)))
        
        vars = build_env.vars
        
        vars['PATH'] = os.pathsep.join([os.path.join(os.path.realpath(os.curdir), 'bin'), os.path.expandvars('${PATH}')])
        
#         conan_storage_path = conans.client.client_cache.ConanClientConfigParser.storage_path
        # TODO: Replace this with the already-configured storage path in Conan
        conan_user_home = os.getenv('CONAN_USER_HOME', '~')
        conan_storage_path = os.path.join(os.path.expanduser(conan_user_home), '.conan', 'data')
        # TODO: use `which pkg-config` to get the full path of the executable
        pkgconfig_exec = 'pkg-config --define-variable conan_storage_path=%s' % (conan_storage_path)
        
        vars['PKG_CONFIG'] = pkgconfig_exec
        
        cpu_count = conans.tools.cpu_count()
        self.output.info('Detected %s cores.' % (cpu_count))
        
        with conans.tools.environment_append(vars):
            self.run('autoreconf --install')
            
            self.output.info('Configuring')
            self.run('%s' % (os.path.join(os.curdir, 'configure')))
            
            self.output.info('Compiling')
            self.run('make -j%s' % (cpu_count))
            
            executables = [os.path.join(os.curdir, 'src', 'main')]
            if self.scope.dev:
                self.output.info('Dumping object information')
                for executable in executables:
                    if conans.tools.os_info.is_windows:
                        pass
                    elif conans.tools.os_info.is_macos:
                        self.run('otool -l %s' % executable)
                    else:
                        self.run('objdump -x %s' % executable)
            
            self.output.info('Running test')
            self.run('%s' % (executable))
    
    def test(self):
        executables = [os.path.join(os.curdir, 'src', 'main')]
        for executable in executables:
            self.run('%s' % (executable))
