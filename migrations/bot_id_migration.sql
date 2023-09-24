SET foreign_key_checks = 0;

UPDATE content_bots_new.bot bot
INNER JOIN content_bots_new.bot_mapping map ON bot.tg_id = map.old_tg_id
SET bot.tg_id = map.new_tg_id
WHERE bot.tg_id = map.old_tg_id;

UPDATE content_bots_new.channel channel
INNER JOIN content_bots_new.bot_mapping map ON channel.bot_tg_id = map.old_tg_id
SET channel.bot_tg_id = map.new_tg_id
WHERE channel.bot_tg_id = map.old_tg_id;

UPDATE content_bots_new.post post
INNER JOIN content_bots_new.bot_mapping map ON post.bot_tg_id = map.old_tg_id
SET post.bot_tg_id = map.new_tg_id
WHERE post.bot_tg_id = map.old_tg_id;

UPDATE content_bots_new.user_bot user_bot
INNER JOIN content_bots_new.bot_mapping map ON user_bot.bot_tg_id = map.old_tg_id
SET user_bot.bot_tg_id = map.new_tg_id
WHERE user_bot.bot_tg_id = map.old_tg_id;

SET foreign_key_checks = 1;