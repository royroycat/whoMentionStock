use whoMentionStock;

CREATE TABLE `tweet` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` nvarchar(1000) NOT NULL DEFAULT '',
  `screen_name` nvarchar(1000) NOT NULL DEFAULT '',
  `tweet_id` bigint(64) DEFAULT NULL,
  `tweet` TEXT DEFAULT NULL,
  `url` TEXT DEFAULT NULL,
  `mention_stock` nvarchar(1000) DEFAULT NULL,
  `datetime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE `twitter_user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `username` nvarchar(1000) NOT NULL DEFAULT '',
  `last_request_id` bigint(64) DEFAULT NULL,
  `last_request_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE `stock` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `stock` nvarchar(100) NOT NULL DEFAULT '',
  `keywords` text,
  `last_mention_id` bigint(64) DEFAULT NULL,
  `last_mention_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE `telegram_user` (
  `chat_id` bigint(64) NOT NULL,
  `update_id` bigint(64) NOT NULL,
  `first_name` nvarchar(100) DEFAULT NULL,
  `last_name` nvarchar(100) DEFAULT NULL,
  `username` nvarchar(100) DEFAULT NULL,
  `type` nvarchar(100) DEFAULT NULL,
  `title`nvarchar(1000) DEFAULT NULL,
  `all_are_admin` BOOLEAN,
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`chat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE `ark_trading_info` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `daily_id` int(11) unsigned  NOT NULL,
  `fund` nvarchar(100) NOT NULL DEFAULT '',
  `date` datetime DEFAULT NULL,
  `direction` nvarchar(100) NOT NULL DEFAULT '',
  `ticker` nvarchar(100) DEFAULT NULL,
  `region` nvarchar(100) DEFAULT NULL,
  `cusip` nvarchar(100) DEFAULT NULL,
  `company` nvarchar(1000) DEFAULT NULL,
  `shares` decimal(38,2),
  `etf_percent` decimal(38,6),
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE `ark_fund_holding` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `daily_id` int(11) unsigned  NOT NULL,
  `date` datetime DEFAULT NULL,
  `fund` nvarchar(100) DEFAULT NULL,
  `company` nvarchar(1000) DEFAULT NULL,
  `ticker` nvarchar(100) DEFAULT NULL,
  `cusip` nvarchar(100) DEFAULT NULL,
  `shares` decimal(38,2),
  `market_value` decimal(38,2),
  `weight` decimal(38,2),
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE `config` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` nvarchar(1000) NOT NULL DEFAULT '',
  `value` nvarchar(1000) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_unicode_ci;

insert into stock values (NULL, "NVDA", NULL, NULL, NULL);
insert into stock values (NULL, "TSM", "Taiwan Semiconductor Manufactur", NULL, NULL);
insert into stock values (NULL, "TSLA", "Tesla", NULL, NULL);
insert into twitter_user values (NULL, "BillGates", NULL, NULL);
insert into twitter_user values (NULL, "WarrenBuffett", NULL, NULL);
insert into twitter_user values (NULL, "elonmusk", NULL, NULL);
insert into twitter_user values (NULL, "tim_cook", NULL, NULL);
commit;