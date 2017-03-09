# zlib Conan.io package

This is a repo containing a build file for bundling up [zlib](http://zlib.net) as a [Conan](https://www.conan.io) package.  This does not contain the [actual source code](https://github.com/madler/zlib) for zlib.  It only contains instructions for how to fetch and build it.

This requires having Conan [installed](http://docs.conan.io/en/latest/installation.html) on your build machine.

## Declare the dependency

To use this library in your own project that makes use of Conan, add this line to your `conanfile.txt` in the root of your project:

```text
[requires]
zlib/1.2.11@kent_at_multiscale/stable
```

If you are using the Python configuration file `conanfile.py`:

```python
import conans

class YourProject(conans.ConanFile):
    requires = 'zlib/1.2.11@kent_at_multiscale/stable'
```

Then perform a `conan install` once in your project to pull down the dependency.  You may safely re-run this step at will, but it is only necessary when you change your dependencies.  It is not required for every build.

## Specify options

Zlib has one option for how to build it.  The option is whether to build it as a shared library or a static library.  The default is as a shared library.  If you want it built as a static library instead, add this option to your Conan configuration:

```text
[options]
zlib:shared=False
```

## Use it in your build

Conan can generate integration files for a variety of build systems.  The cleanest integration is using CMake.

### Using CMake

```text
[requires]
zlib/1.2.11@kent_at_multiscale/stable

[generators]
cmake
```

With the above dependency added to your `conanfile.txt` or `conanfile.py` as appropriate, here is an example `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 2.8)

if(CMAKE_VERSION VERSION_LESS 3.1)
project(YourProject C CXX)
else()
project(YourProject LANGUAGES CXX)
endif()

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
if(CMAKE_VERSION VERSION_LESS 3.1.2)
conan_basic_setup()
else()
conan_basic_setup(TARGETS)
endif()

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CMAKE_SKIP_RPATH OFF)
set(CMAKE_MACOSX_RPATH ON)
set(CMAKE_SKIP_BUILD_RPATH ON)
set(CMAKE_SKIP_INSTALL_RPATH OFF)
set(CMAKE_BUILD_WITH_INSTALL_RPATH ON)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH OFF)

add_executable(your_executable your_source.cpp)

if(CMAKE_VERSION VERSION_LESS 3.1.2)
target_link_libraries(your_executable ${CONAN_LIBS})
else()
target_link_libraries(your_executable CONAN_PKG::zlib)
endif()

if(CMAKE_VERSION VERSION_LESS 3.1)
set_target_properties(your_executable PROPERTIES
    COMPILE_OPTIONS "-std=c++11"
)
else()
set_target_properties(your_executable PROPERTIES
    CXX_EXTENSIONS OFF
    CXX_STANDARD 11
    CXX_STANDARD_REQUIRED ON
)
endif()

if(APPLE)
set_property(TARGET your_executable APPEND PROPERTY INSTALL_RPATH "@executable_path/../lib")
elseif(WIN32)
# No @rpath on Windows.
else()
set_property(TARGET your_executable APPEND PROPERTY INSTALL_RPATH "\$ORIGIN/../lib")
endif()
```

The `include` and `conan_basic_setup` pull in the dependencies declared in your Conan configuration file.

The `target_link_libraries` uses the `CONAN_PKG::zlib` or `${CONAN_LIBS}` to automatically pull in headers, libraries, compile flags, and link flags specified by the package itself.

### Using Autotools

```text
[requires]
zlib/1.2.11@kent_at_multiscale/stable

[generators]
env
txt
```

You will need to set up a couple of environment variables in order to build properly.

```bash
CONAN_USER_HOME=~
PKG_CONFIG=pkg-config --define-variable conan_storage_path=${CONAN_USER_HOME}/.conan/data
PKG_CONFIG_PATH=${CONAN_USER_HOME}/.conan/data/zlib/1.2.11-12/multiscalehn/stable/package/${PACKAGE_ID}/lib/pkgconfig
```

You can set all of these things much more easily if you use `conanfile.py` and define your own `build` method:

```python
import conans

class YourProject(conans.ConanFile):
    requires = 'zlib/1.2.11@kent_at_multiscale/stable'
    
    def imports(self):
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
        
        rpath = []
        if conans.tools.os_info.is_macos:
            rpath.append('@executable_path/../lib')
        elif conans.tools.os_info.is_windows:
            pass
        else:
            rpath.append('\\$$ORIGIN/../lib')
        
        for p in rpath:
            build_env.link_flags.append('-Wl,-rpath,%s' % (p))
        
        vars = build_env.vars
        
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
```

Here is an example `configure.ac`:

```m4
AC_PREREQ([2.69])
AC_INIT([your_project], [1.0.0], [your_email@your_domain.com])
AM_INIT_AUTOMAKE([-Wall -Werror foreign])
AC_CONFIG_FILES([Makefile src/Makefile])

AC_PROG_CXX

PKG_CHECK_MODULES([ZLIB], [zlib = 1.2.11])

AC_OUTPUT
```

Then in your `src/Makefile.am`:

```make
bin_PROGRAMS = your_executable

your_executable_SOURCES = your_source.cpp
your_executable_CXXFLAGS = $(ZLIB_CFLAGS)
your_executable_LDADD = $(ZLIB_LIBS)
your_executable_LDFLAGS = -Wl,-rpath,@executable_path/../lib -Wl,-rpath,\$$ORIGIN/../lib
```

Technically this does not actually use the Conan integration directly.  However, it does make use of the `zlib.pc` file included in the package.

## Controlling the build

There are a few Conan scopes you can use to modify the build process.  These will not change the generated binaries in any way.

If you pass `--scope ALL:verbose=True`, the build will be verbose.

If you pass `--scope ALL:skipTest=True`, it will skip building and running the tests.

If you pass `--scope ALL:installTools=True`, it will attempt to install any system-level tools needed for the build.

## Note: This is not needed for development.

There is no need for you to clone this repository in order to make use of this package.  Simply declaring the dependency in your Conan configuration is sufficient.  The only reason to clone this repository is to change how we build the package.

If you do clone this repository, you can make local changes and then expose your local changes to other projects on your machine by using `conan export`.  These changes will persist on your local machine but will not be available to any other machines unless you explicitly perform a `conan upload`.
