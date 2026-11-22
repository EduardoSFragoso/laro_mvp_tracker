/*
Yellow Tracker — initial database structure and seed data
Server: Ragnarök Online LATAM (ro.gnjoylatam.com)

MVP list based on the community tracker data for Ragnarok Online LATAM
(names and respawn windows as seen in-game, in pt-BR).
id_mob holds the mob id used for the track table thumbnail (ratemyserver.net);
it may be NULL, in which case no thumbnail is shown.

Command to (re)apply the MVP seed on an existing database: sql/seed_mvp_latam.sql
*/

DROP TABLE IF EXISTS mvp_guild_log;
DROP TABLE IF EXISTS mvp_guild;
DROP TABLE IF EXISTS mvp_alias;
DROP TABLE IF EXISTS mvp;
DROP TABLE IF EXISTS guild;
DROP TABLE IF EXISTS global_parameter;
DROP SEQUENCE IF EXISTS mvp_seq;

CREATE SEQUENCE mvp_seq;

CREATE TABLE global_parameter (
    id bigint NOT NULL,
    race_time timestamp without time zone,
    CONSTRAINT global_parameter_pk PRIMARY KEY (id)
);

CREATE TABLE guild (
    id bigint NOT NULL,
    custom boolean NOT NULL DEFAULT TRUE,
    mobile boolean NOT NULL DEFAULT FALSE,
    timezone text,
    id_mvp_channel bigint,
    id_notification_role bigint,
    CONSTRAINT guild_pk PRIMARY KEY (id)
);

CREATE TABLE mvp (
    id integer NOT NULL DEFAULT nextval('mvp_seq'::regclass),
    name text NOT NULL,
    map text NOT NULL,
    navi text,
    t1 integer NOT NULL,
    t2 integer NOT NULL,
    t1custom integer,
    t2custom integer,
    id_mob integer,
    CONSTRAINT mvp_pk PRIMARY KEY (id)
);

CREATE TABLE mvp_alias (
    id_mvp integer NOT NULL,
    alias text NOT NULL,
    CONSTRAINT mvp_alias_pk PRIMARY KEY (id_mvp, alias)
);

CREATE TABLE mvp_guild (
    id_mvp integer NOT NULL,
    id_guild bigint NOT NULL,
    track_time timestamp without time zone NOT NULL,
    CONSTRAINT mvp_guild_pk PRIMARY KEY (id_mvp, id_guild)
);

CREATE TABLE mvp_guild_log (
    id_mvp integer NOT NULL,
    id_guild bigint NOT NULL,
    id_user bigint NOT NULL,
    date timestamp without time zone NOT NULL,
    CONSTRAINT mvp_guild_log_pk PRIMARY KEY (id_mvp, id_guild)
);

INSERT INTO global_parameter(id)VALUES(1);

-- ---------------------------------------------------------------------------
-- MVPs (Ragnarok Online LATAM) — name, map, min/max respawn (mins), mob id
-- ---------------------------------------------------------------------------

INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Abelha-Rainha','Monte Mjolnir (4)','mjolnir_04',120,130,1059);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Mistress');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Amon Ra','Subsolo da Pirâmide (2)','moc_pryd06',60,70,1511);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Amon Ra do Pesadelo','Subsolo da Pirâmide (2) - Pesadelo','moc_prydn2',60,70,2362);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Nightmare Amon Ra');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Aranha Rainha','Porão de Glastheim','gl_cas01_',120,130,20421);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Brinaranea');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Árvore de Pitaya','Estufa de Pitayas','ba_lost',360,370,20648);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Pitaya');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Atroce','Planície de Ida','ra_fild03',180,190,1785);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Atroce Ida');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Atroce','Pradaria Audhumbla','ra_fild04',300,310,1785);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Atroce Audhumbla');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Atroce','Arredores de Veins (1)','ve_fild01',180,190,1785);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Atroce Veins');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Atroce','Arredores de Veins (2)','ve_fild02',360,370,1785);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Atroce Veins 2');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Bafomé','Labirinto da Floresta (3)','prt_maze03',120,130,1039);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Baphomet');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Bafomé Amaldiçoado','Castelo Amaldiçoado','gl_cas02_',120,130,2483);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Cursed Baphomet');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Belzebu','Monastério (3)','abbey03',720,730,1873);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Beelzebub');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Besouro-Ladrão Dourado','Esgotos de Prontera (4)','prt_sewb4',60,70,1086);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'GTB');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Golden Thief Bug');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Bispo Decadente','Monastério (2)','abbey02',120,130,1871);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'FBH');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Fallen Bishop');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Boitatá','Profundezas das Cataratas','bra_dun02',120,130,2068);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Boitata');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Bruxa da Morte','Calabouço de Niflheim - Ópera em Ruínas','nif_dun02',180,190,NULL);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Death Witch');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Cavaleiro da Tempestade','Fábrica de Brinquedos (2)','xmas_dun02',67,77,1251);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'SK');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Stormy Knight');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Detale Esqueleto','Caverna Subterrânea do Lago do Abismo (4)','abyss_04',180,190,20618);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Skeleton Detale');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Detardeurus','Caverna Subterrânea do Lago do Abismo (3)','abyss_03',180,190,1719);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Detale');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Doppelganger','Calabouço de Geffen (2)','gef_dun02',120,130,1046);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Drácula','Calabouço de Geffen (1)','gef_dun01',60,70,1389);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Dracula');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Drake','Navio Fantasma (2)','treasure02',120,130,1112);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Eddga','Floresta de Payon (10)','pay_fild11',120,130,1115);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Espadachim Egnigem','Biolaboratório (2)','lhz_dun02',120,130,1658);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'GEC');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Egnigem Cenia');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Faraó','Esfinge (5)','in_sphinx5',60,70,1157);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Pharaoh');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Flor do Luar','Caverna de Payon (4)','pay_dun04',60,70,1150);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'MF');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Moonlight Flower');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Freeoni','Deserto de Sograt (17)','moc_fild17',120,130,1159);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Phreeoni');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Gemaring','Ninho do Dragão (1)','lasa_dun01',60,70,3505);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('General Tartaruga','Palácio Tartaruga','tur_dun04',60,70,1312);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'TG');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Turtle General');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Gorynych','Floresta Encantada (3)','mosk_dun03',120,130,NULL);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Hatii','Arredores de Lutie','xmas_fild01',120,130,1252);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Garm');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Ifrit','Vulcão de Thor (3)','thor_v03',660,670,1832);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Imperatriz Scaraba','Caverna Scaraba - Pesadelo','dic_dun03',120,130,NULL);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Empress Scaraba');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Jungoliant','Calabouço da Mina (3)','ein_dun03',120,130,20601);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Jewel Ungoliant');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Kiel-D-01','Fábrica de Robôs (2)','kh_dun02',120,180,1734);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Kiel');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Kraken','Túnel Submarino (5)','iz_dun05',140,150,2202);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Lady Branca','Suei Long Gon','lou_dun03',116,126,1630);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'WL');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'White Lady');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Bacsojin');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Lady Tanee','Santuário Ancestral','ayo_dun02',420,430,1688);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'LT');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Tanee');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Leak','Vulcão Krakatau','dew_dun01',120,130,2156);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Lorde das Trevas','Porão de Glastheim','gl_chyard',60,70,1272);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Dark Lord');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Maya','Formigueiro Infernal (2)','anthell02',120,130,1147);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Morroc Ferido','Deserto de Sograt (22)','moc_fild22',720,730,1917);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'WM');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Wounded Morroc');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Muspellskoll','Caverna de Magma (3)','mag_dun03',120,130,NULL);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Skoll');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Orc Herói','Arredores de Geffen (3)','gef_fild03',60,70,1087);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'OH');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Orc Hero');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Osíris','Pirâmide (4)','moc_pryd04',60,70,1038);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Osiris');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Pesar Noturno','Santuário de Freya (5)','ra_san05',300,310,1768);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Gloom Under Night');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Presas Flamejantes','Labirinto de Oz (2)','oz_dun02',360,370,NULL);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Burning Fang');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Quimera Única','Laboratório Abandonado de Amicitia','amicitia2',180,190,NULL);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Chimeratheone');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Quimera Venenosa','Laboratório Werner','slabw01',60,70,3633);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Venomous Chimera');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('R001-Bestia','Rudus 4º Andar - Área de Descarte de Experimentos','sp_rudus4',180,190,20934);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('R48-85-Bestia','Rudus, depósito de rejeitos (2)','sp_rudus2',60,70,20381);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Rainha Scaraba','Caverna Scaraba','dic_dun02',120,130,2087);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'QS');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Queen Scaraba');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Rei Goblin','Câmara Desconhecida da Torre do Relógio','clock_01',1200,1210,NULL);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Goblin King');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('RSX-0806','Calabouço da Mina (2)','ein_dun02',125,135,1623);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Samurai Encarnado','Templo Subterrâneo','ama_dun03',91,101,1542);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Samurai Specter');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Senhor das Trevas','Cemitério de Glastheim','gl_chyard',60,70,1272);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Dark Lord');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Senhor das Trevas','Cemitério Amaldiçoado','gl_chyard_',60,70,1272);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Dark Lord');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Senhor dos Mortos','Nifflheim','niflheim',133,143,1373);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'LOD');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Lord of the Dead');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Senhor dos Orcs','Arredores de Geffen (10)','gef_fild10',120,130,1190);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'OL');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Orc Lord');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Serpente Suprema','Terra das Fadas','gon_dun03',94,104,1418);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'ESL');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Evil Snake Lord');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Tao Gunka','Karu, a Caverna do Oeste','beach_dun',300,310,1583);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Tao');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Valquíria Randgris','Templo de Odin (3)','odin_tem03',480,490,1765);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'VR');
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Valkyrie Randgris');
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Vesper','Centro de Juperos','jupe_core',120,130,1685);
INSERT INTO mvp(name,map,navi,t1,t2,id_mob)VALUES('Vigia do Tempo','Torre Distorcida (3)','c_tower3_',120,130,3074);
INSERT INTO mvp_alias(id_mvp,alias)VALUES(currval('mvp_seq'),'Time Holder');
