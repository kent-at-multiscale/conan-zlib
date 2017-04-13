import glob
import os
import shutil
import subprocess
import tempfile

import conans


class ZlibConan(conans.ConanFile):
    """
    A Conan recipe for building zlib.
    """
    name = 'zlib'
    external_version_major = 1
    external_version_minor = 2
    external_version_patch = 11
    external_version = '%s.%s.%s' % (external_version_major, external_version_minor, external_version_patch)
    external_tag = 'v%s' % (external_version)
    version = '%s' % external_version
    description = 'The zlib library.'
    url = 'git@github.com:kent-at-multiscale/conan-zlib.git'
    license = 'http://zlib.net/zlib_license.html'
    author = 'Kent Rosenkoetter <kent.rosenkoetter@multiscalehn.com>'
    settings = 'os', 'compiler', 'build_type', 'arch'
    generators = 'env'
    options = {
        'shared': [True, False]
        }
    default_options = 'shared=True'
    
    def configure(self):
        """
        Using different compilers and build types will produce different binaries.
        However, the C++ standard library makes no difference since this is pure
        C code.  Therefore, remove libcxx from the data used to compute the ID.
        """
        del self.settings.compiler.libcxx
    
    def system_requirements(self):
        if self.scope.installTools:
            try:
                installer = conans.tools.SystemPackageTool()
                installer.update()
                installer.install('autoconf')
                installer.install('automake')
                installer.install('git')
                installer.install('libtool')
                installer.install('make')
                installer.install('pkg-config')
            except:
                self.output.warn('Unable to bootstrap required build tools.  If they are already installed, you can ignore this warning.')
    
    def source(self):
#         self.run('git clone https://github.com/madler/zlib.git -b %s' % (self.external_tag))
        zip_name = 'zlib-1.2.11.tar.gz'
        conans.tools.download('http://zlib.net/%s' % zip_name, zip_name)
        conans.tools.check_sha256(zip_name, 'c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1')
        conans.tools.unzip(zip_name)
        shutil.move('zlib-1.2.11', 'zlib')
        os.remove(zip_name)
    
    def build(self):
        build_env = conans.AutoToolsBuildEnvironment(self)
        build_env.fpic = True
        
        rpath = []
        if conans.tools.os_info.is_macos:
            rpath.append('@loader_path/')
        elif conans.tools.os_info.is_windows:
            pass
        else:
            pass
        
        for p in rpath:
            build_env.link_flags.append('-Wl,-rpath,%s' % (p))
        
        vars = build_env.vars
        
#         conan_storage_path = conans.client.client_cache.ConanClientConfigParser.storage_path
        # TODO: Replace this with the already-configured storage path in Conan
        conan_user_home = os.getenv('CONAN_USER_HOME', '~')
        conan_storage_path = os.path.join(os.path.expanduser(conan_user_home), '.conan', 'data')
        # TODO: use `which pkg-config` to get the full path of the executable
        pkgconfig_exec = 'pkg-config --define-variable conan_storage_path=%s' % (conan_storage_path)
        
        vars['PKG_CONFIG'] = pkgconfig_exec
        
        configure_flags = []
        if self.options.shared:
            configure_flags.append('--enable-shared')
        else:
            configure_flags.append('--static')
        
        if self.settings.build_type == 'Debug':
            configure_flags.append('--debug')
        
        configure_flags.append('--warn')
        
        cpu_count = conans.tools.cpu_count()
        self.output.info('Detected %s cores.' % (cpu_count))
        
        # This edits the configure script so that dynamic libraries built
        # on Mac are named using @rpath rather than the absolute path of where
        # they were originally installed.  This is to make them relocatable.
        if conans.tools.os_info.is_macos:
            conans.tools.replace_in_file(os.path.join(os.curdir, 'zlib', 'configure'), '-install_name $libdir/$SHAREDLIBM', '-install_name @rpath/$SHAREDLIBM')
        
        with conans.tools.environment_append(vars):
            # TODO: check for Windows and run appropriately
            self.output.info('Configuring')
            self.run('%s --prefix="%s" %s' % (os.path.join(os.curdir, 'configure'), self.package_folder, ' '.join(configure_flags)), cwd='zlib')
            
            self.output.info('Compiling')
            self.run('make -j%s' % (cpu_count), cwd='zlib')
            
            if not self.scope.skipTest:
                self.output.info('Running tests')
                self.run('make -j%s check' % (cpu_count), cwd='zlib')
            
            self.output.info('Installing into Conan package folder %s' % (self.package_folder))
            self.run('make install', cwd='zlib')
    
    def package(self):
#         conan_storage_path = conans.client.client_cache.ConanClientConfigParser.storage_path
        # TODO: Replace this with the already-configured storage path in Conan
        conan_user_home = os.getenv('CONAN_USER_HOME', '~')
        conan_storage_path = os.path.join(os.path.expanduser(conan_user_home), '.conan', 'data')
        # If there are configuration files for pkg-config, they will contain
        # hard-coded paths where the library was installed.
        # We need to remove those and replace them with a placeholder that
        # Conan can fill in on any other machine as appropriate.
        for libdir in ['lib', 'share']:
            pkgconfig_dir = os.path.join(self.package_folder, libdir, 'pkgconfig')
            if os.path.isdir(pkgconfig_dir):
                pkgconfig_pattern = os.path.join(pkgconfig_dir, '*.pc')
                for pkgconfig_file in glob.iglob(pkgconfig_pattern):
                    self.output.info('Stripping Conan storage directory (%s) from pkg-config file %s' % (conan_storage_path, pkgconfig_file))
                    _, tempname = tempfile.mkstemp()
                    with open(tempname, 'w') as output:
                        with open(pkgconfig_file, 'r') as input:
                            # TODO: replace this with something pkg-config can expand automatically
                            output.write('conan_storage_path=~/.conan/data\n')
                            for line in input:
                                output.write(line)
                    shutil.move(tempname, pkgconfig_file)
                    conans.tools.replace_in_file(pkgconfig_file, conan_storage_path, '${conan_storage_path}')
        
        libdir = os.path.join(self.package_folder, 'lib')
        
        # We want to remove the libtool metadata for both static and shared libraries.
        # Conan is intended to solve the metadata problem, and it does a better
        # job than libtool does.
        if os.path.isdir(libdir):
            for libtool_file in glob.iglob(os.path.join(libdir, '*.la')):
                self.output.info('Deleting libtool metadata %s' % (libtool_file))
                os.remove(libtool_file)
    
    def package_info(self):
        self.cpp_info.includedirs = ['include']  # Ordered list of include paths
        self.cpp_info.libs = []  # The libs to link against
        self.cpp_info.libdirs = ['lib']  # Directories where libraries can be found
        self.cpp_info.resdirs = []  # Directories where resources, data, etc can be found
        self.cpp_info.bindirs = []  # Directories where executables and shared libs can be found
        self.cpp_info.defines = []  # preprocessor definitions
        self.cpp_info.cflags = []  # pure C flags
        self.cpp_info.cppflags = []  # C++ compilation flags
        self.cpp_info.sharedlinkflags = []  # linker flags
        self.cpp_info.exelinkflags = []  # linker flags
        
        # pkg_config_path is a custom variable we add to the existing Conan env_info
        self.env_info.PKG_CONFIG_PATH = []
        for libdir in ['lib', 'share']:
            pkgconfig_dir = os.path.join(self.package_folder, libdir, 'pkgconfig')
            if os.path.isdir(pkgconfig_dir):
                self.env_info.PKG_CONFIG_PATH.append(pkgconfig_dir)
                pkgconfig_pattern = os.path.join(pkgconfig_dir, '*.pc')
                for pkgconfig_file in glob.iglob(pkgconfig_pattern):
                    with open(pkgconfig_file, 'r') as input:
                        for line in input:
                            if str(line).startswith('Libs:'):
                                line = line[5:]
                                for ele in line.split():
                                    if str(ele).startswith('-L'):
                                        pass
                                    elif str(ele).startswith('-l'):
                                        library = ele[2:]
                                        if not library in self.cpp_info.libs:
                                            self.cpp_info.libs.append(library)
                                    elif str(ele).startswith('-D'):
                                        define = ele[2:]
                                        if not define in self.cpp_info.defines:
                                            self.cpp_info.defines.append(define)
                                    else:
                                        flag = ele
                                        if not flag in self.cpp_info.sharedlinkflags:
                                            self.cpp_info.sharedlinkflags.append(flag)
                                        if not flag in self.cpp_info.exelinkflags:
                                            self.cpp_info.exelinkflags.append(flag)
                            elif str(line).startswith('Cflags:'):
                                line = line[7:]
                                for ele in line.split():
                                    if str(ele).startswith('-I'):
                                        pass
                                    elif str(ele).startswith('-D'):
                                        define = ele[2:]
                                        if not define in self.cpp_info.defines:
                                            self.cpp_info.defines.append(define)
                                    else:
                                        flag = ele
                                        if not flag in self.cpp_info.cflags:
                                            self.cpp_info.cflags.append(flag)
                                        if not flag in self.cpp_info.cppflags:
                                            self.cpp_info.cppflags.append(flag)
        
        for includedir in self.cpp_info.includedirs:
            self.output.info('%s include dir: %s' % (self.name, includedir))
        self.output.info('%s libs: %s' % (self.name, self.cpp_info.libs))
        for libdir in self.cpp_info.libdirs:
            self.output.info('%s lib dir: %s' % (self.name, libdir))
        for resdir in self.cpp_info.resdirs:
            self.output.info('%s resource dir: %s' % (self.name, resdir))
        for bindir in self.cpp_info.bindirs:
            self.output.info('%s bin dir: %s' % (self.name, bindir))
        self.output.info('%s defines: %s' % (self.name, self.cpp_info.defines))
        self.output.info('%s cflags: %s' % (self.name, self.cpp_info.cflags))
        self.output.info('%s cppflags: %s' % (self.name, self.cpp_info.cppflags))
        self.output.info('%s sharedlinkflags: %s' % (self.name, self.cpp_info.sharedlinkflags))
        self.output.info('%s exelinkflags: %s' % (self.name, self.cpp_info.exelinkflags))
