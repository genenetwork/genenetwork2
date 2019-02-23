## ChangeLog v2.11 pre-release (date unknown)

This is a massive bug fix release with many improvements. For contributions
see
[contributors](https://github.com/genenetwork/genenetwork2/contributors)
and
[commits](https://github.com/genenetwork/genenetwork2/commits/master).

The current GNU Guix checkout is at

https://gitlab.com/genenetwork/guix-bioinformatics/tree/gn-latest-20190213

and

https://gitlab.com/genenetwork/guix/tree/gn-latest-20190213

With these branches a binary install can be fetched with

    env GUIX_PACKAGE_PATH=../guix-bioinformatics ./pre-inst-env guix package --substitute-urls="https://berlin.guixsd.org http://guix.genenetwork.org https://mirror.hydra.gnu.org" -i genenetwork2 -p ~/opt/gn-latest-20190213

The key for guix.genenetwork.org is

```scheme
(public-key
 (ecc
  (curve Ed25519)
  (q #D54AA5C8CBE268CBC82418AB83709611BAC88B39D44E68C18F6E16197B5B5CA0#)
  )
 )
```

### Migrated PIL to pillow (preparing for Python3 migration)

### Dropped pylmm support

### Added GEMMA support

* Front-end support

### Added test framework and unit tests

* Added python integration and unit tests
