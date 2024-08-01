;;; This file describes a Guix system container to run the database
;;; services required by genenetwork2 locally on your own
;;; machine. This is to allow a purely offline development setup for
;;; hacking on genenetwork2. To build and run the container, use
;;; db-container.sh.

(use-modules (gnu)
             (gnu packages databases)
             (gnu services databases))

(define %mariadb-state-directory
  "/var/lib/mysql")

(define set-permissions-gexp
  (with-imported-modules '((guix build utils))
    #~(begin
        (use-modules (guix build utils))

        ;; Set ownership of mariadb state directory.
        (let ((user (getpw "mysql")))
          (for-each (lambda (file)
                      (chown file (passwd:uid user) (passwd:gid user)))
                    (find-files #$%mariadb-state-directory #:directories? #t))))))

(operating-system
  (host-name "genenetwork2")
  (timezone "Etc/UTC")
  (locale "en_US.utf8")
  (bootloader (bootloader-configuration
               (bootloader grub-bootloader)
               (targets (list "does-not-matter"))))
  (file-systems %base-file-systems)
  (packages (cons mariadb  ;; for the mysql CLI client
                  %base-packages))
  (services (cons* (service mysql-service-type)
                   (service redis-service-type)
                   (simple-service 'set-permissions
                                   activation-service-type
                                   set-permissions-gexp)
                   %base-services)))
