;; Make sure you have the
;; https://git.genenetwork.org/guix-bioinformatics/guix-bioinformatics
;; channel set up.
;;
;; To drop into a development environment, run
;;
;; guix shell -Df guix.scm
;;
;; To get a development environment in a container, run
;;
;; guix shell -C -Df guix.scm

(define-module (genenetwork2))
(use-modules (gn packages genenetwork)
             (guix gexp)
             (guix utils)
             (guix git-download)
             (guix packages)
             (ice-9 popen)
             (ice-9 rdelim))

(define %source-dir
  (string-append (current-source-directory)
                 "/../.."))

;; This isn't kept up-to-date.
(define %version
  (call-with-input-file (string-append %source-dir "/VERSION")
    (lambda (port)
      (read-line port))))

(define (%version package)
  (or (version-major+minor+point (package-version package))
      (version-major+minor (package-version package))))

(define-public genenetwork2-head
  (package
    (inherit genenetwork2)
    (version (string-append (%version genenetwork2) "-HEAD"))
    (source (local-file %source-dir "genenetwork2-checkout"
                        #:recursive? #t
                        #:select? (or (git-predicate %source-dir)
                                      (const #t))))))

genenetwork2-head
