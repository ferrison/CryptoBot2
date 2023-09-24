SET foreign_key_checks = 0;

USE content_bots_new;



DELETE FROM content_bots_new.button WHERE post_id IN (SELECT id FROM content_bots_new.post WHERE date < '2023-05-15');
DELETE FROM content_bots_new.message WHERE post_id IN (SELECT id FROM content_bots_new.post WHERE date < '2023-05-15');
DELETE FROM content_bots_new.media WHERE post_id IN (SELECT id FROM content_bots_new.post WHERE date < '2023-05-15');

DELETE FROM content_bots_new.post WHERE date < '2023-05-15';

SET foreign_key_checks = 1;