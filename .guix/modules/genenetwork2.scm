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

(define-module (genenetwork2)
  #:use-module ((gn packages genenetwork)
                #:select (genenetwork2) #:prefix gn:)
  #:use-module (guix gexp)
  #:use-module (guix utils)
  #:use-module (guix git-download)
  #:use-module (guix packages))

(define %source-dir
  (string-append (current-source-directory)
                 "/../.."))

(define-public genenetwork2
  (package
    (inherit gn:genenetwork2)
    (source (local-file %source-dir "genenetwork2-checkout"
                        #:recursive? #t
                        #:select? (or (git-predicate %source-dir)
                                      (const #t))))))

genenetwork2
