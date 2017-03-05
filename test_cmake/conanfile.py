import os

import conans


class CMakeZlibUser(conans.ConanFile):
    """
    This tests the zlib package by building an application that links to it.
    This uses CMake to build.
    """
    settings = 'os', 'compiler', 'build_type', 'arch'
    exports_sources = 'CMakeLists.txt', 'main.cpp'
    requires = 'zlib/1.2.11-1@kent_at_multiscale/stable'
    generators = 'cmake', 'env', 'txt'
    
    def system_requirements(self):
        if self.scope.installTools:
            try:
                installer = conans.tools.SystemPackageTool()
                installer.update()
                installer.install('cmake')
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
        cmake = conans.CMake(self.settings)
        
        cmake_flags = []
        if self.scope.verbose:
            cmake_flags.append('-DCMAKE_VERBOSE_MAKEFILE=ON')
        else:
            cmake_flags.append('-DCMAKE_VERBOSE_MAKEFILE=OFF')
        
        cpu_count = conans.tools.cpu_count()
        self.output.info('Detected %s CPUs' % cpu_count)
        
        self.output.info('Creating build scripts')
        self.run('cmake "%s" %s %s' % (self.conanfile_directory, cmake.command_line, ' '.join(cmake_flags)))
        
        self.output.info('Compiling')
        self.run('cmake --build "%s" %s -- -j%s' % (os.curdir, cmake.build_config, cpu_count))
        
        if self.scope.dev:
            self.output.info('Dumping object information')
            executable = os.path.join(os.curdir, 'bin', 'main')
            if conans.tools.os_info.is_windows:
                pass
            elif conans.tools.os_info.is_macos:
                self.run('otool -l %s' % executable)
            else:
                self.run('objdump -x %s' % executable)
        
        self.output.info('Running tests')
        self.run('ctest --parallel %s' % (cpu_count))
    
    def test(self):
        cpu_count = conans.tools.cpu_count()
        self.output.info('Detected %s CPUs' % cpu_count)
        
        self.output.info('Running tests')
        self.run('ctest --parallel %s' % (cpu_count))
