# Maintainer: Evan Callicoat <apsu@propter.net>
pkgname=aur-builder-git
_gitname=aur-builder
pkgver=0.0.0
pkgrel=1
pkgdesc="A collection of tools for building/maintaining AUR packages and repos."
arch=('x86_64')
url="http://github.com/Apsu/aur-builder"
license=('GPL')
depends=('turbolift' 'libxslt' 'cower' 'expac' 'btrfs-progs' 'systemd>=204')
makedepends=('git')
provides=('aur-builder')
conflicts=('aur-builder')
source=('git://github.com/Apsu/aur-builder.git')
md5sums=('SKIP')

pkgver() {
  cd $_gitname
  # Use the tag of the last commit
  git describe --always | sed 's|-|.|g'
}

#build() {
#  cd $_gitname
#
#}

package() {
  cd $_gitname

  #install things
}
