FROM gleif/webs:latest

EXPOSE 7678

CMD ["/usr/local/var/webs/scripts/webs-resolver-service.sh"]