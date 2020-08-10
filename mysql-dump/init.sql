use whoMentionStock;

CREATE TABLE `tweet` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `tweet` varchar(1000) DEFAULT NULL,
  `datetime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `twitter` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(1000) NOT NULL DEFAULT '',
  `last_request_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `stock` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `stock` varchar(100) NOT NULL DEFAULT '',
  `keywords` text,
  `last_request_id` bigint(64) DEFAULT NULL,
  `last_request_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

insert into stock values (NULL, "NVDA", NULL, NULL, NULL);
insert into stock values (NULL, "TSM", "Taiwan Semiconductor Manufactur", NULL, NULL);
insert into twitter values (NULL, "BillGates", NULL);
insert into twitter values (NULL, "WarrenBuffett", NULL);
insert into twitter values (NULL, "elonmusk", NULL);
insert into twitter values (NULL, "Apple", NULL);
commit;