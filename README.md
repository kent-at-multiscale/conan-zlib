# zlib Conan.io package

This is a repo containing a build file for bundling up [zlib](http://zlib.net) as [Conan](https://www.conan.io) packages.  This does not contain the actual source code for zlib.  It only contains instructions for how to fetch and build it.

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

class YourProject(conan.ConanFile):
    requires = 'zlib/1.2.11@kent_at_multiscale/stable'
```

Then perform a `conan install` once in your project to pull down the dependency.  You may safely re-run this step at will, but it is only necessary when you change your dependencies.  It is not required for every build.

## Specify options

Zlib has one option for how to build it.  The option is whether to build it as a shared library or a static library.  The default is as a shared library.  If you want it built as a static library instead, add this option to your Conan configuration:

```text
zlib:shared=False
```

## Controlling the build

There are a few Conan scopes you can use to modify the build process.  These will not change the generated binaries in any way.

If you pass `--scope verbose=True`, the build will be verbose.

If you pass `--scope skipTest=True`, it will skip building and running the tests.

If you pass `--scope installTools=True`, it will attempt to install any system-level tools needed for the build.

## Note: This is not needed for development.

There is no need for you to clone this repository in order to make use of this package.  Simply declaring the dependency in your Conan configuration is sufficient.  The only reason to clone this repository is to change how to build the package.

If you do clone this repository, you can make local changes and then expose your local changes to other projects on your machine by using `conan export`.  These changes will persist on your local machine but will not be available to any other machines unless you explicitly perform a `conan upload`.
