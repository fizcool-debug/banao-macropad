pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'banao'
gnome = import('gnome')

gnome.compile_resources('banao',
  'banao.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'banao.in',
  output: 'banao',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

# Root source files
install_data([
  '__init__.py',
  'main.py',
], install_dir: moduledir)

# Core package files
install_data([
  'core/__init__.py',
  'core/profile_engine.py',
  'core/serial_reader.py',
  'core/engine.py',
], install_dir: moduledir / 'core')

# Adapters package files
install_data([
  'adapters/__init__.py',
  'adapters/base.py',
  'adapters/linux.py',
  'adapters/windows.py',
  'adapters/factory.py',
], install_dir: moduledir / 'adapters')

# UI package files
install_data([
  'ui/__init__.py',
  'ui/window.py',
  'ui/tray_helper.py',
], install_dir: moduledir / 'ui')
