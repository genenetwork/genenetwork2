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

(use-modules (gn packages genenetwork)
             (guix gexp)
             (guix git-download)
             (guix packages))

(define %source-dir (dirname (current-filename)))

(package
  (inherit genenetwork2)
  (source (local-file %source-dir "genenetwork2-checkout"
                      #:recursive? #t
                      #:select? (git-predicate %source-dir))))
