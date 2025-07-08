--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8 (Debian 16.8-1.pgdg120+1)
-- Dumped by pg_dump version 16.9 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: categorias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categorias (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    nombre character varying(50) NOT NULL,
    parent_id uuid,
    nivel integer DEFAULT 0 NOT NULL,
    activo boolean DEFAULT true NOT NULL
);


ALTER TABLE public.categorias OWNER TO postgres;

--
-- Name: cuotas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cuotas (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    servicio_id uuid NOT NULL,
    nombre character varying(100) NOT NULL,
    limite_uso integer DEFAULT 0 NOT NULL,
    plan_stripe character varying(255),
    activo boolean DEFAULT true
);


ALTER TABLE public.cuotas OWNER TO postgres;

--
-- Name: items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.items (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    receipt_id uuid,
    nombre character varying(100) NOT NULL,
    precio numeric(10,2) NOT NULL,
    cantidad integer NOT NULL,
    categoria_id uuid,
    sub_categoria_id uuid
);


ALTER TABLE public.items OWNER TO postgres;

--
-- Name: servicios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.servicios (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion character varying(255),
    activo boolean DEFAULT true
);


ALTER TABLE public.servicios OWNER TO postgres;

--
-- Name: ticket; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ticket (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    nombre_tienda character varying(100) NOT NULL,
    total numeric(10,2) NOT NULL,
    usuario_id uuid,
    created_at timestamp without time zone NOT NULL,
    modified_at timestamp without time zone NOT NULL
);


ALTER TABLE public.ticket OWNER TO postgres;

--
-- Name: uso_servicios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.uso_servicios (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    usuario_id uuid NOT NULL,
    servicio_id uuid NOT NULL,
    cuota_id uuid NOT NULL,
    uso_actual integer DEFAULT 0,
    ultimo_reset timestamp with time zone
);


ALTER TABLE public.uso_servicios OWNER TO postgres;

--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    nombre character varying(100) NOT NULL,
    apellidos character varying(100) NOT NULL,
    correo character varying(100) NOT NULL,
    customer_id character varying(255) NOT NULL,
    active boolean DEFAULT true,
    passw character varying(72) NOT NULL,
    subscription_id character varying(255),
    last_verified timestamp with time zone
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Data for Name: categorias; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.categorias (id, nombre, parent_id, nivel, activo) FROM stdin;
'5755ba46-b134-4a1a-a0ed-71d0e821917b'	Electrónica y Computación	\N	0	t
'5755ba46-b134-4a1a-a0ed-71d0e821917b'	Electrónica y Computación	\N	0	t
'5755ba46-b134-4a1a-a0ed-71d0e821917b'	Electrónica y Computación	\N	0	t
'c6675918-a440-4bb4-92af-0763e61d0d9d'	Ordenadores y Portátiles	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'c6675918-a440-4bb4-92af-0763e61d0d9d'	Ordenadores y Portátiles	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'c6675918-a440-4bb4-92af-0763e61d0d9d'	Ordenadores y Portátiles	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'8e86ad04-305c-4de2-babf-0e42e5875946'	Tablets y E-readers	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'8e86ad04-305c-4de2-babf-0e42e5875946'	Tablets y E-readers	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'8e86ad04-305c-4de2-babf-0e42e5875946'	Tablets y E-readers	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'2beda887-a53d-4f71-b6ad-7f4422dffe16'	Componentes de PC	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'2beda887-a53d-4f71-b6ad-7f4422dffe16'	Componentes de PC	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'2beda887-a53d-4f71-b6ad-7f4422dffe16'	Componentes de PC	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'af2e327a-197e-4569-9765-78e0f8cdd017'	Monitores y Pantallas	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'af2e327a-197e-4569-9765-78e0f8cdd017'	Monitores y Pantallas	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'af2e327a-197e-4569-9765-78e0f8cdd017'	Monitores y Pantallas	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'cd2b8f91-a58e-40e7-a93a-2165772ed992'	Periféricos	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'cd2b8f91-a58e-40e7-a93a-2165772ed992'	Periféricos	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'cd2b8f91-a58e-40e7-a93a-2165772ed992'	Periféricos	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'1b4b3c1d-57ad-47e2-af0f-06c329ae998a'	Almacenamiento	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'1b4b3c1d-57ad-47e2-af0f-06c329ae998a'	Almacenamiento	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'1b4b3c1d-57ad-47e2-af0f-06c329ae998a'	Almacenamiento	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'0b96c2f4-7446-4607-b579-2b62703580c1'	Redes y Conectividad	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'0b96c2f4-7446-4607-b579-2b62703580c1'	Redes y Conectividad	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'0b96c2f4-7446-4607-b579-2b62703580c1'	Redes y Conectividad	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'a4606084-ab2d-4fff-b008-e3b5668bc17e'	Impresoras y Escáneres	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'a4606084-ab2d-4fff-b008-e3b5668bc17e'	Impresoras y Escáneres	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'a4606084-ab2d-4fff-b008-e3b5668bc17e'	Impresoras y Escáneres	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'f0b27613-6218-4728-aaac-7bfa327b5874'	Accesorios Electrónicos	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'f0b27613-6218-4728-aaac-7bfa327b5874'	Accesorios Electrónicos	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'f0b27613-6218-4728-aaac-7bfa327b5874'	Accesorios Electrónicos	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'6f74e61c-e93d-4d90-b4ba-630b9b842aea'	Domótica y Smart Home	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'6f74e61c-e93d-4d90-b4ba-630b9b842aea'	Domótica y Smart Home	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'6f74e61c-e93d-4d90-b4ba-630b9b842aea'	Domótica y Smart Home	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'dacb1a08-8fc6-4891-9906-f478e7987c0e'	Dispositivos de Energía Sostenible	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'dacb1a08-8fc6-4891-9906-f478e7987c0e'	Dispositivos de Energía Sostenible	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'dacb1a08-8fc6-4891-9906-f478e7987c0e'	Dispositivos de Energía Sostenible	5755ba46-b134-4a1a-a0ed-71d0e821917b	1	t
'b15e64db-768a-4fb8-a7d8-18f8e8d90dca'	Electrodomésticos	\N	0	t
'b15e64db-768a-4fb8-a7d8-18f8e8d90dca'	Electrodomésticos	\N	0	t
'b15e64db-768a-4fb8-a7d8-18f8e8d90dca'	Electrodomésticos	\N	0	t
'34cdfe94-0ca0-435c-ba2a-e5cd720f89cc'	Grandes Electrodomésticos	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'34cdfe94-0ca0-435c-ba2a-e5cd720f89cc'	Grandes Electrodomésticos	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'34cdfe94-0ca0-435c-ba2a-e5cd720f89cc'	Grandes Electrodomésticos	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'c0e0cbcc-0c04-4ca0-b1eb-ebc85b1a4414'	Pequeños Electrodomésticos de Cocina	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'c0e0cbcc-0c04-4ca0-b1eb-ebc85b1a4414'	Pequeños Electrodomésticos de Cocina	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'c0e0cbcc-0c04-4ca0-b1eb-ebc85b1a4414'	Pequeños Electrodomésticos de Cocina	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'bb64950d-07d0-437f-a638-2b5a376c72bc'	Electrodomésticos de Clima	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'bb64950d-07d0-437f-a638-2b5a376c72bc'	Electrodomésticos de Clima	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'bb64950d-07d0-437f-a638-2b5a376c72bc'	Electrodomésticos de Clima	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'c407b6f3-cd2b-4878-8cec-933f264a4aaa'	Aspiradoras y Limpieza	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'c407b6f3-cd2b-4878-8cec-933f264a4aaa'	Aspiradoras y Limpieza	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'c407b6f3-cd2b-4878-8cec-933f264a4aaa'	Aspiradoras y Limpieza	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'e5df00a6-824c-460e-b7ae-69942e92b4c4'	Planchado	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'e5df00a6-824c-460e-b7ae-69942e92b4c4'	Planchado	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'e5df00a6-824c-460e-b7ae-69942e92b4c4'	Planchado	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'7036557d-ae91-4372-88f7-02e08ff2977e'	Electrodomésticos de Baño	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'7036557d-ae91-4372-88f7-02e08ff2977e'	Electrodomésticos de Baño	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'7036557d-ae91-4372-88f7-02e08ff2977e'	Electrodomésticos de Baño	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'74e56af3-ade4-4987-ac6c-d4a519300a12'	Electrodomésticos para el Cuidado Personal	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'74e56af3-ade4-4987-ac6c-d4a519300a12'	Electrodomésticos para el Cuidado Personal	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'74e56af3-ade4-4987-ac6c-d4a519300a12'	Electrodomésticos para el Cuidado Personal	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'06a98eff-165b-4c7a-a46b-92f50182ede2'	Purificadores y Humidificadores	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'06a98eff-165b-4c7a-a46b-92f50182ede2'	Purificadores y Humidificadores	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'06a98eff-165b-4c7a-a46b-92f50182ede2'	Purificadores y Humidificadores	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'a10df964-8244-4deb-b8ca-b577c02c71e4'	Electrodomésticos de Bajo Consumo	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'a10df964-8244-4deb-b8ca-b577c02c71e4'	Electrodomésticos de Bajo Consumo	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'a10df964-8244-4deb-b8ca-b577c02c71e4'	Electrodomésticos de Bajo Consumo	b15e64db-768a-4fb8-a7d8-18f8e8d90dca	1	t
'522eb07d-53e8-4a19-98b1-e9c819c5ec5c'	Telefonía y Comunicaciones	\N	0	t
522eb07d-53e8-4a19-98b1-e9c819c5ec5c	Telefonía y Comunicaciones	\N	0	t
522eb07d-53e8-4a19-98b1-e9c819c5ec5c	Telefonía y Comunicaciones	\N	0	t
b52b50d9-7721-4e6a-9f9c-1051b9d37b18	Smartphones	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
b52b50d9-7721-4e6a-9f9c-1051b9d37b18	Smartphones	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
b52b50d9-7721-4e6a-9f9c-1051b9d37b18	Smartphones	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
66a7a2a0-9f8a-4a3c-a5a2-c557a2c70596	Teléfonos Fijos	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
66a7a2a0-9f8a-4a3c-a5a2-c557a2c70596	Teléfonos Fijos	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
66a7a2a0-9f8a-4a3c-a5a2-c557a2c70596	Teléfonos Fijos	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
f85c0f51-54ca-4dfa-8a75-de9cae145df3	Accesorios para Móviles	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
f85c0f51-54ca-4dfa-8a75-de9cae145df3	Accesorios para Móviles	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
f85c0f51-54ca-4dfa-8a75-de9cae145df3	Accesorios para Móviles	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
ae1506b9-cc15-4922-9578-c3bb93d661ce	Smartwatches y Wearables	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
ae1506b9-cc15-4922-9578-c3bb93d661ce	Smartwatches y Wearables	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
ae1506b9-cc15-4922-9578-c3bb93d661ce	Smartwatches y Wearables	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
f1018d0d-8c96-4c3c-99c6-5dbb36205f2e	Tarjetas SIM y Planes	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
f1018d0d-8c96-4c3c-99c6-5dbb36205f2e	Tarjetas SIM y Planes	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
f1018d0d-8c96-4c3c-99c6-5dbb36205f2e	Tarjetas SIM y Planes	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
7a873256-8788-4b47-a8cb-882d9755cb0a	Radios y Walkie-talkies	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
7a873256-8788-4b47-a8cb-882d9755cb0a	Radios y Walkie-talkies	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
7a873256-8788-4b47-a8cb-882d9755cb0a	Radios y Walkie-talkies	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
8fbcfaaa-5bcd-40ea-bcb6-7e923728eadc	Fax y Telefonía IP	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
8fbcfaaa-5bcd-40ea-bcb6-7e923728eadc	Fax y Telefonía IP	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
8fbcfaaa-5bcd-40ea-bcb6-7e923728eadc	Fax y Telefonía IP	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
0cdf09a8-0cf6-443f-abad-8569f7ab4f27	Dispositivos de Comunicación Satelital	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
0cdf09a8-0cf6-443f-abad-8569f7ab4f27	Dispositivos de Comunicación Satelital	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
0cdf09a8-0cf6-443f-abad-8569f7ab4f27	Dispositivos de Comunicación Satelital	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
c16f33aa-cc92-4f82-a60e-6324cfc549c8	Accesorios Sostenibles para Dispositivos	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
c16f33aa-cc92-4f82-a60e-6324cfc549c8	Accesorios Sostenibles para Dispositivos	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
c16f33aa-cc92-4f82-a60e-6324cfc549c8	Accesorios Sostenibles para Dispositivos	522eb07d-53e8-4a19-98b1-e9c819c5ec5c	1	t
d107f994-12d6-45f2-8b6b-cecf0e774d8e	Audio, Video y Fotografía	\N	0	t
d107f994-12d6-45f2-8b6b-cecf0e774d8e	Audio, Video y Fotografía	\N	0	t
d107f994-12d6-45f2-8b6b-cecf0e774d8e	Audio, Video y Fotografía	\N	0	t
e99c72df-8566-4d43-bc93-822be388736e	Televisores	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
e99c72df-8566-4d43-bc93-822be388736e	Televisores	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
e99c72df-8566-4d43-bc93-822be388736e	Televisores	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
2afd03e0-192b-437e-9bde-156e089c4bb9	Equipos de Sonido	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
2afd03e0-192b-437e-9bde-156e089c4bb9	Equipos de Sonido	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
2afd03e0-192b-437e-9bde-156e089c4bb9	Equipos de Sonido	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
df69fe39-e039-4044-b8af-4fdcd3a44e39	Altavoces y Barras de Sonido	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
df69fe39-e039-4044-b8af-4fdcd3a44e39	Altavoces y Barras de Sonido	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
df69fe39-e039-4044-b8af-4fdcd3a44e39	Altavoces y Barras de Sonido	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
b37fd779-0457-41ee-b6b1-54d97dcbe8ac	Auriculares y Cascos	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
b37fd779-0457-41ee-b6b1-54d97dcbe8ac	Auriculares y Cascos	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
b37fd779-0457-41ee-b6b1-54d97dcbe8ac	Auriculares y Cascos	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
93d1d7d0-6c85-4b3a-9220-1e4a49a79390	Cámaras Fotográficas	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
93d1d7d0-6c85-4b3a-9220-1e4a49a79390	Cámaras Fotográficas	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
93d1d7d0-6c85-4b3a-9220-1e4a49a79390	Cámaras Fotográficas	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
dc2db7e1-cde1-43d8-902d-ab9ad81b9607	Videocámaras	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
dc2db7e1-cde1-43d8-902d-ab9ad81b9607	Videocámaras	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
dc2db7e1-cde1-43d8-902d-ab9ad81b9607	Videocámaras	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
475a73da-b698-4504-b195-262e5df43245	Accesorios Fotográficos	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
475a73da-b698-4504-b195-262e5df43245	Accesorios Fotográficos	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
475a73da-b698-4504-b195-262e5df43245	Accesorios Fotográficos	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
5b41e5aa-7daa-4d88-90d7-dd2a2e5aac4c	Proyectores	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
5b41e5aa-7daa-4d88-90d7-dd2a2e5aac4c	Proyectores	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
5b41e5aa-7daa-4d88-90d7-dd2a2e5aac4c	Proyectores	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
95bce589-4da4-4c2e-90af-c9ef6957467a	Reproductores Multimedia	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
95bce589-4da4-4c2e-90af-c9ef6957467a	Reproductores Multimedia	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
95bce589-4da4-4c2e-90af-c9ef6957467a	Reproductores Multimedia	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
a83fc612-1192-4eaa-be99-e3ba9368b91d	Drones con Cámara	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
a83fc612-1192-4eaa-be99-e3ba9368b91d	Drones con Cámara	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
a83fc612-1192-4eaa-be99-e3ba9368b91d	Drones con Cámara	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
60ab3a64-370f-4bfb-abc0-637ff6aecd70	Equipos Audiovisuales de Bajo Consumo	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
60ab3a64-370f-4bfb-abc0-637ff6aecd70	Equipos Audiovisuales de Bajo Consumo	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
60ab3a64-370f-4bfb-abc0-637ff6aecd70	Equipos Audiovisuales de Bajo Consumo	d107f994-12d6-45f2-8b6b-cecf0e774d8e	1	t
faebd740-7b46-434b-b64f-51eb6f1e0966	Videojuegos y Entretenimiento Digital	\N	0	t
faebd740-7b46-434b-b64f-51eb6f1e0966	Videojuegos y Entretenimiento Digital	\N	0	t
faebd740-7b46-434b-b64f-51eb6f1e0966	Videojuegos y Entretenimiento Digital	\N	0	t
85b61b61-b5b1-41fb-b839-3f58e9765cf7	Consolas	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
85b61b61-b5b1-41fb-b839-3f58e9765cf7	Consolas	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
85b61b61-b5b1-41fb-b839-3f58e9765cf7	Consolas	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
57a4ba94-4f12-49a0-935d-1f7e626560d4	Videojuegos	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
57a4ba94-4f12-49a0-935d-1f7e626560d4	Videojuegos	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
57a4ba94-4f12-49a0-935d-1f7e626560d4	Videojuegos	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
2f60b79e-cc5b-4460-a75f-d924284391cf	Accesorios para Consolas	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
2f60b79e-cc5b-4460-a75f-d924284391cf	Accesorios para Consolas	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
2f60b79e-cc5b-4460-a75f-d924284391cf	Accesorios para Consolas	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
3ea9612c-6a3e-4fa9-b403-570e07bf5147	Juegos para PC	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
3ea9612c-6a3e-4fa9-b403-570e07bf5147	Juegos para PC	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
3ea9612c-6a3e-4fa9-b403-570e07bf5147	Juegos para PC	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
f7b2c79f-4a39-48c2-8d92-070b78ccb4b6	Realidad Virtual	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
f7b2c79f-4a39-48c2-8d92-070b78ccb4b6	Realidad Virtual	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
f7b2c79f-4a39-48c2-8d92-070b78ccb4b6	Realidad Virtual	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
bf7cd280-acf0-44d9-a5f5-3707ba07e56c	Streaming y Contenido Digital	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
bf7cd280-acf0-44d9-a5f5-3707ba07e56c	Streaming y Contenido Digital	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
bf7cd280-acf0-44d9-a5f5-3707ba07e56c	Streaming y Contenido Digital	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
a0a7f1e8-76da-4cd1-bbf0-a09890dd9bb0	Tarjetas Prepago y Suscripciones	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
a0a7f1e8-76da-4cd1-bbf0-a09890dd9bb0	Tarjetas Prepago y Suscripciones	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
a0a7f1e8-76da-4cd1-bbf0-a09890dd9bb0	Tarjetas Prepago y Suscripciones	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
3bf24318-c778-46cb-8d57-99713a23a1c3	Gaming PC y Equipamiento	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
3bf24318-c778-46cb-8d57-99713a23a1c3	Gaming PC y Equipamiento	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
3bf24318-c778-46cb-8d57-99713a23a1c3	Gaming PC y Equipamiento	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
d5c678b3-1a17-4519-be8e-90b111bcd589	Retro Gaming	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
d5c678b3-1a17-4519-be8e-90b111bcd589	Retro Gaming	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
d5c678b3-1a17-4519-be8e-90b111bcd589	Retro Gaming	faebd740-7b46-434b-b64f-51eb6f1e0966	1	t
614709fb-f263-45f0-9e43-f9274f46052f	Moda y Accesorios	\N	0	t
614709fb-f263-45f0-9e43-f9274f46052f	Moda y Accesorios	\N	0	t
614709fb-f263-45f0-9e43-f9274f46052f	Moda y Accesorios	\N	0	t
b51f653f-ff57-4a5d-b513-6d5e57736cf6	Ropa para Mujer	614709fb-f263-45f0-9e43-f9274f46052f	1	t
b51f653f-ff57-4a5d-b513-6d5e57736cf6	Ropa para Mujer	614709fb-f263-45f0-9e43-f9274f46052f	1	t
b51f653f-ff57-4a5d-b513-6d5e57736cf6	Ropa para Mujer	614709fb-f263-45f0-9e43-f9274f46052f	1	t
cf8ccff1-50a2-40d7-b0f1-4c195e38265f	Ropa para Hombre	614709fb-f263-45f0-9e43-f9274f46052f	1	t
cf8ccff1-50a2-40d7-b0f1-4c195e38265f	Ropa para Hombre	614709fb-f263-45f0-9e43-f9274f46052f	1	t
cf8ccff1-50a2-40d7-b0f1-4c195e38265f	Ropa para Hombre	614709fb-f263-45f0-9e43-f9274f46052f	1	t
073ee689-fce4-426c-9615-d8fc9bcde16f	Ropa Infantil	614709fb-f263-45f0-9e43-f9274f46052f	1	t
073ee689-fce4-426c-9615-d8fc9bcde16f	Ropa Infantil	614709fb-f263-45f0-9e43-f9274f46052f	1	t
073ee689-fce4-426c-9615-d8fc9bcde16f	Ropa Infantil	614709fb-f263-45f0-9e43-f9274f46052f	1	t
4bcfd0a0-57bb-4b07-b103-7f439f434dca	Calzado	614709fb-f263-45f0-9e43-f9274f46052f	1	t
4bcfd0a0-57bb-4b07-b103-7f439f434dca	Calzado	614709fb-f263-45f0-9e43-f9274f46052f	1	t
4bcfd0a0-57bb-4b07-b103-7f439f434dca	Calzado	614709fb-f263-45f0-9e43-f9274f46052f	1	t
fa8e5f5a-01b4-421e-9418-a584c3fe4ef3	Bolsos y Mochilas	614709fb-f263-45f0-9e43-f9274f46052f	1	t
fa8e5f5a-01b4-421e-9418-a584c3fe4ef3	Bolsos y Mochilas	614709fb-f263-45f0-9e43-f9274f46052f	1	t
fa8e5f5a-01b4-421e-9418-a584c3fe4ef3	Bolsos y Mochilas	614709fb-f263-45f0-9e43-f9274f46052f	1	t
c182fa6c-176b-4d68-8885-b9b89e90ed96	Relojes	614709fb-f263-45f0-9e43-f9274f46052f	1	t
c182fa6c-176b-4d68-8885-b9b89e90ed96	Relojes	614709fb-f263-45f0-9e43-f9274f46052f	1	t
c182fa6c-176b-4d68-8885-b9b89e90ed96	Relojes	614709fb-f263-45f0-9e43-f9274f46052f	1	t
040f6a63-695e-4c12-a450-de33f2d9c4c8	Joyería y Bisutería	614709fb-f263-45f0-9e43-f9274f46052f	1	t
040f6a63-695e-4c12-a450-de33f2d9c4c8	Joyería y Bisutería	614709fb-f263-45f0-9e43-f9274f46052f	1	t
040f6a63-695e-4c12-a450-de33f2d9c4c8	Joyería y Bisutería	614709fb-f263-45f0-9e43-f9274f46052f	1	t
b45ccbc1-0c93-4a84-8dd5-8180f5d34371	Complementos	614709fb-f263-45f0-9e43-f9274f46052f	1	t
b45ccbc1-0c93-4a84-8dd5-8180f5d34371	Complementos	614709fb-f263-45f0-9e43-f9274f46052f	1	t
b45ccbc1-0c93-4a84-8dd5-8180f5d34371	Complementos	614709fb-f263-45f0-9e43-f9274f46052f	1	t
391b54fc-cd0e-4e3a-8399-bc8de92f8b64	Gafas y Lentes	614709fb-f263-45f0-9e43-f9274f46052f	1	t
391b54fc-cd0e-4e3a-8399-bc8de92f8b64	Gafas y Lentes	614709fb-f263-45f0-9e43-f9274f46052f	1	t
391b54fc-cd0e-4e3a-8399-bc8de92f8b64	Gafas y Lentes	614709fb-f263-45f0-9e43-f9274f46052f	1	t
7ad694f3-2224-4804-8cb6-44d75b846dc4	Ropa Deportiva	614709fb-f263-45f0-9e43-f9274f46052f	1	t
7ad694f3-2224-4804-8cb6-44d75b846dc4	Ropa Deportiva	614709fb-f263-45f0-9e43-f9274f46052f	1	t
7ad694f3-2224-4804-8cb6-44d75b846dc4	Ropa Deportiva	614709fb-f263-45f0-9e43-f9274f46052f	1	t
048c0856-0705-4b30-959d-b010ee1e9aa2	Ropa Interior y Baño	614709fb-f263-45f0-9e43-f9274f46052f	1	t
048c0856-0705-4b30-959d-b010ee1e9aa2	Ropa Interior y Baño	614709fb-f263-45f0-9e43-f9274f46052f	1	t
048c0856-0705-4b30-959d-b010ee1e9aa2	Ropa Interior y Baño	614709fb-f263-45f0-9e43-f9274f46052f	1	t
fdfd5311-62e4-4f0b-98de-a6f87d8d349b	Moda Sostenible y Ecológica	614709fb-f263-45f0-9e43-f9274f46052f	1	t
fdfd5311-62e4-4f0b-98de-a6f87d8d349b	Moda Sostenible y Ecológica	614709fb-f263-45f0-9e43-f9274f46052f	1	t
fdfd5311-62e4-4f0b-98de-a6f87d8d349b	Moda Sostenible y Ecológica	614709fb-f263-45f0-9e43-f9274f46052f	1	t
81a8e876-da7a-48e0-b2cd-208492bf6082	Accesorios de Materiales Reciclados	614709fb-f263-45f0-9e43-f9274f46052f	1	t
81a8e876-da7a-48e0-b2cd-208492bf6082	Accesorios de Materiales Reciclados	614709fb-f263-45f0-9e43-f9274f46052f	1	t
81a8e876-da7a-48e0-b2cd-208492bf6082	Accesorios de Materiales Reciclados	614709fb-f263-45f0-9e43-f9274f46052f	1	t
da247399-7b6d-4624-980f-0b03925845d7	Belleza y Cuidado Personal	\N	0	t
da247399-7b6d-4624-980f-0b03925845d7	Belleza y Cuidado Personal	\N	0	t
da247399-7b6d-4624-980f-0b03925845d7	Belleza y Cuidado Personal	\N	0	t
25cddd8a-e0b5-4fd4-9c74-5ae78b0950e3	Maquillaje	da247399-7b6d-4624-980f-0b03925845d7	1	t
25cddd8a-e0b5-4fd4-9c74-5ae78b0950e3	Maquillaje	da247399-7b6d-4624-980f-0b03925845d7	1	t
25cddd8a-e0b5-4fd4-9c74-5ae78b0950e3	Maquillaje	da247399-7b6d-4624-980f-0b03925845d7	1	t
f59e49e6-4070-43f0-aaec-dfa6f5e7c5cd	Cuidado Facial	da247399-7b6d-4624-980f-0b03925845d7	1	t
f59e49e6-4070-43f0-aaec-dfa6f5e7c5cd	Cuidado Facial	da247399-7b6d-4624-980f-0b03925845d7	1	t
f59e49e6-4070-43f0-aaec-dfa6f5e7c5cd	Cuidado Facial	da247399-7b6d-4624-980f-0b03925845d7	1	t
86d82de4-2753-4d76-b0f7-c208dc77d51e	Cuidado Corporal	da247399-7b6d-4624-980f-0b03925845d7	1	t
86d82de4-2753-4d76-b0f7-c208dc77d51e	Cuidado Corporal	da247399-7b6d-4624-980f-0b03925845d7	1	t
86d82de4-2753-4d76-b0f7-c208dc77d51e	Cuidado Corporal	da247399-7b6d-4624-980f-0b03925845d7	1	t
aceee7bc-d0ff-4375-b6ce-def705f81d33	Perfumes y Fragancias	da247399-7b6d-4624-980f-0b03925845d7	1	t
aceee7bc-d0ff-4375-b6ce-def705f81d33	Perfumes y Fragancias	da247399-7b6d-4624-980f-0b03925845d7	1	t
aceee7bc-d0ff-4375-b6ce-def705f81d33	Perfumes y Fragancias	da247399-7b6d-4624-980f-0b03925845d7	1	t
e95d641b-1833-4d95-ac78-840a6d5cea8f	Cuidado del Cabello	da247399-7b6d-4624-980f-0b03925845d7	1	t
e95d641b-1833-4d95-ac78-840a6d5cea8f	Cuidado del Cabello	da247399-7b6d-4624-980f-0b03925845d7	1	t
e95d641b-1833-4d95-ac78-840a6d5cea8f	Cuidado del Cabello	da247399-7b6d-4624-980f-0b03925845d7	1	t
1b4df18f-da08-42f6-a941-0f57e50870b5	Manicura y Pedicura	da247399-7b6d-4624-980f-0b03925845d7	1	t
1b4df18f-da08-42f6-a941-0f57e50870b5	Manicura y Pedicura	da247399-7b6d-4624-980f-0b03925845d7	1	t
1b4df18f-da08-42f6-a941-0f57e50870b5	Manicura y Pedicura	da247399-7b6d-4624-980f-0b03925845d7	1	t
25ef8cf6-73ca-4b00-ab81-bd7bf7f5dae5	Afeitado y Depilación	da247399-7b6d-4624-980f-0b03925845d7	1	t
25ef8cf6-73ca-4b00-ab81-bd7bf7f5dae5	Afeitado y Depilación	da247399-7b6d-4624-980f-0b03925845d7	1	t
25ef8cf6-73ca-4b00-ab81-bd7bf7f5dae5	Afeitado y Depilación	da247399-7b6d-4624-980f-0b03925845d7	1	t
92bc6746-69ba-4327-b847-6db3690e92f5	Higiene Personal	da247399-7b6d-4624-980f-0b03925845d7	1	t
92bc6746-69ba-4327-b847-6db3690e92f5	Higiene Personal	da247399-7b6d-4624-980f-0b03925845d7	1	t
92bc6746-69ba-4327-b847-6db3690e92f5	Higiene Personal	da247399-7b6d-4624-980f-0b03925845d7	1	t
939e4f7c-9e30-462b-9e9e-2ac3bc5cb90c	Cosmética Natural	da247399-7b6d-4624-980f-0b03925845d7	1	t
939e4f7c-9e30-462b-9e9e-2ac3bc5cb90c	Cosmética Natural	da247399-7b6d-4624-980f-0b03925845d7	1	t
939e4f7c-9e30-462b-9e9e-2ac3bc5cb90c	Cosmética Natural	da247399-7b6d-4624-980f-0b03925845d7	1	t
14dc7b82-cb3d-41ad-a8bd-92ce1e0e0c50	Cuidado Dental	da247399-7b6d-4624-980f-0b03925845d7	1	t
14dc7b82-cb3d-41ad-a8bd-92ce1e0e0c50	Cuidado Dental	da247399-7b6d-4624-980f-0b03925845d7	1	t
14dc7b82-cb3d-41ad-a8bd-92ce1e0e0c50	Cuidado Dental	da247399-7b6d-4624-980f-0b03925845d7	1	t
65e88f20-31fe-44df-b840-c0695ff666b7	Cosmética Ecológica y Sostenible	da247399-7b6d-4624-980f-0b03925845d7	1	t
65e88f20-31fe-44df-b840-c0695ff666b7	Cosmética Ecológica y Sostenible	da247399-7b6d-4624-980f-0b03925845d7	1	t
65e88f20-31fe-44df-b840-c0695ff666b7	Cosmética Ecológica y Sostenible	da247399-7b6d-4624-980f-0b03925845d7	1	t
8cfae1a0-f75e-4072-ac89-a6435290d794	Salud y Bienestar	\N	0	t
8cfae1a0-f75e-4072-ac89-a6435290d794	Salud y Bienestar	\N	0	t
8cfae1a0-f75e-4072-ac89-a6435290d794	Salud y Bienestar	\N	0	t
8dc172c5-ec3d-4dde-a4b7-7a550041938d	Medicamentos	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
8dc172c5-ec3d-4dde-a4b7-7a550041938d	Medicamentos	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
8dc172c5-ec3d-4dde-a4b7-7a550041938d	Medicamentos	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
3dffb30f-ed6f-401d-b213-47b18f9d6a78	Suplementos y Vitaminas	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
3dffb30f-ed6f-401d-b213-47b18f9d6a78	Suplementos y Vitaminas	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
3dffb30f-ed6f-401d-b213-47b18f9d6a78	Suplementos y Vitaminas	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
2fb5346c-4a13-4e99-adb2-8bb2787025e3	Primeros Auxilios	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
2fb5346c-4a13-4e99-adb2-8bb2787025e3	Primeros Auxilios	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
2fb5346c-4a13-4e99-adb2-8bb2787025e3	Primeros Auxilios	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
c648d386-01be-4f79-8850-bd148cf5cf77	Cuidado de la Salud en el Hogar	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
c648d386-01be-4f79-8850-bd148cf5cf77	Cuidado de la Salud en el Hogar	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
c648d386-01be-4f79-8850-bd148cf5cf77	Cuidado de la Salud en el Hogar	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
4be279a6-23f4-4d8a-a0ca-ec239bfa6d38	Ortopedia y Movilidad	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
4be279a6-23f4-4d8a-a0ca-ec239bfa6d38	Ortopedia y Movilidad	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
4be279a6-23f4-4d8a-a0ca-ec239bfa6d38	Ortopedia y Movilidad	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
bc651971-acaa-442a-a081-cc550e7d8a80	Terapias Alternativas	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
bc651971-acaa-442a-a081-cc550e7d8a80	Terapias Alternativas	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
bc651971-acaa-442a-a081-cc550e7d8a80	Terapias Alternativas	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
6897e207-4bea-4b8c-aef4-c2a15b915fa8	Control de Peso	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
6897e207-4bea-4b8c-aef4-c2a15b915fa8	Control de Peso	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
6897e207-4bea-4b8c-aef4-c2a15b915fa8	Control de Peso	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
76398aab-cfc0-41f2-b5d2-ce517827e093	Equipamiento Médico Profesional	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
76398aab-cfc0-41f2-b5d2-ce517827e093	Equipamiento Médico Profesional	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
76398aab-cfc0-41f2-b5d2-ce517827e093	Equipamiento Médico Profesional	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
c235ff5c-22b6-48c5-bacb-beb97ad0610b	Atención Especializada	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
c235ff5c-22b6-48c5-bacb-beb97ad0610b	Atención Especializada	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
c235ff5c-22b6-48c5-bacb-beb97ad0610b	Atención Especializada	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
27cb2f78-9fba-4317-b63c-0496d7605f98	Audífonos y Salud Auditiva	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
27cb2f78-9fba-4317-b63c-0496d7605f98	Audífonos y Salud Auditiva	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
27cb2f78-9fba-4317-b63c-0496d7605f98	Audífonos y Salud Auditiva	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
93661fc6-81c6-49a1-9fea-eb6a3add899f	Suplementos Naturales y Ecológicos	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
93661fc6-81c6-49a1-9fea-eb6a3add899f	Suplementos Naturales y Ecológicos	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
93661fc6-81c6-49a1-9fea-eb6a3add899f	Suplementos Naturales y Ecológicos	8cfae1a0-f75e-4072-ac89-a6435290d794	1	t
93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	Alimentos y Bebidas	\N	0	t
93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	Alimentos y Bebidas	\N	0	t
93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	Alimentos y Bebidas	\N	0	t
41d71736-8e92-491f-af3f-54d4e5f64af1	Alimentos No Perecederos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
41d71736-8e92-491f-af3f-54d4e5f64af1	Alimentos No Perecederos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
41d71736-8e92-491f-af3f-54d4e5f64af1	Alimentos No Perecederos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
59a75ebb-eb67-4a43-b063-211d1dbf7337	Snacks y Aperitivos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
59a75ebb-eb67-4a43-b063-211d1dbf7337	Snacks y Aperitivos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
59a75ebb-eb67-4a43-b063-211d1dbf7337	Snacks y Aperitivos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
2b267cac-56fb-417d-9ace-26adeabde56e	Bebidas Alcohólicas	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
2b267cac-56fb-417d-9ace-26adeabde56e	Bebidas Alcohólicas	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
2b267cac-56fb-417d-9ace-26adeabde56e	Bebidas Alcohólicas	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
e91011d9-ba95-413b-8853-65cfffd9b675	Bebidas No Alcohólicas	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
e91011d9-ba95-413b-8853-65cfffd9b675	Bebidas No Alcohólicas	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
e91011d9-ba95-413b-8853-65cfffd9b675	Bebidas No Alcohólicas	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
70830fd9-d781-426b-8b82-29c5b11772d4	Frutería y Verdulería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
70830fd9-d781-426b-8b82-29c5b11772d4	Frutería y Verdulería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
70830fd9-d781-426b-8b82-29c5b11772d4	Frutería y Verdulería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
c065ba8d-a11d-4445-a67e-f9061313410e	Carnicería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
c065ba8d-a11d-4445-a67e-f9061313410e	Carnicería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
c065ba8d-a11d-4445-a67e-f9061313410e	Carnicería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
efaeece6-1aa2-4265-b961-1308cd4aa898	Pescadería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
efaeece6-1aa2-4265-b961-1308cd4aa898	Pescadería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
efaeece6-1aa2-4265-b961-1308cd4aa898	Pescadería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
2d3d4f88-15c0-474e-bac8-816bf4c447cd	Charcutería y Embutidos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
2d3d4f88-15c0-474e-bac8-816bf4c447cd	Charcutería y Embutidos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
2d3d4f88-15c0-474e-bac8-816bf4c447cd	Charcutería y Embutidos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
b4c1a410-ae10-46ac-bf52-92141ef8b932	Lácteos y Huevos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
b4c1a410-ae10-46ac-bf52-92141ef8b932	Lácteos y Huevos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
b4c1a410-ae10-46ac-bf52-92141ef8b932	Lácteos y Huevos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
0cca1eb3-0939-4695-b379-635e25af984b	Panadería y Repostería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
0cca1eb3-0939-4695-b379-635e25af984b	Panadería y Repostería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
0cca1eb3-0939-4695-b379-635e25af984b	Panadería y Repostería	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
f15b1192-710a-4872-8980-9ce583afdc26	Congelados	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
f15b1192-710a-4872-8980-9ce583afdc26	Congelados	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
f15b1192-710a-4872-8980-9ce583afdc26	Congelados	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
7ecb0a74-daf9-4a17-973d-ee5fb13d91c2	Productos Gourmet y Delicatessen	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
1d3f5eb7-d555-49d5-a180-fb3e9e6c4784	Alimentación Especializada	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
71607119-6750-436d-ba40-c1d7fe86ef6a	Aceites, Vinagres y Condimentos	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
546fbe1c-a403-4b09-89cc-46b90db949a3	Desayuno y Cereales	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
9842d7e1-cfe6-4803-987e-961ea2c758dd	Alimentación Ecológica y Orgánica	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
82f789cb-9321-41fd-90ac-e52138ff2050	Productos Locales y de Proximidad	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	1	t
cdfe1569-7a66-473f-9e0b-41be1044ea42	Hogar, Muebles y Decoración	\N	0	t
11a0a13b-e03b-4986-89af-6e33cea0c075	Muebles de Salón	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
c462e102-d86e-401f-bb3a-cf4b396df617	Muebles de Dormitorio	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
7af1b02a-ec92-4268-874a-bebe08972ed1	Muebles de Cocina	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
1bba512a-ef33-48f9-8d6b-75a85d6a111a	Muebles de Oficina	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
2f8ec6f9-371a-4a22-8e4f-c626eb4525ec	Decoración e Interiorismo	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
0822392d-8e1e-4b99-b8d3-2b1b8de26bb9	Iluminación	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
4d53fc57-adc7-43bd-b967-2ec1925e0c78	Textiles del Hogar	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
dc4d1be1-3689-4461-a25b-e572d3fc60da	Utensilios de Cocina	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
63b782e7-b6f5-44a2-aa28-29f0f2627f69	Vajilla y Cubertería	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
3a1d9657-e594-4648-9aef-75ae1513594d	Organización y Almacenaje	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
57d0bdf4-6cd5-4072-97fc-924e02fd1a88	Muebles de Materiales Sostenibles	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
f65a20a9-4122-4b45-95d2-a98ad95e9047	Decoración Ecológica	cdfe1569-7a66-473f-9e0b-41be1044ea42	1	t
ad4f2bcf-5d17-424a-883c-d18811e71618	Jardín y Exterior	\N	0	t
0d81365d-ad56-4ee7-9cdb-f5970e24c17f	Muebles de Jardín	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
09df582b-0aad-4507-af9a-f2211fc2b7e4	Herramientas de Jardinería	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
3f5e4d76-5d89-4a19-b554-395dd83db42f	Plantas y Semillas	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
4f9ff497-898c-461d-9e53-5e0f548cd7e0	Piscinas y Accesorios	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
a01a5337-5dde-4a2c-b8e7-6baf12e97e0f	Barbacoas y Parrillas	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
981fc5df-bd6e-4bfb-8e8e-cf748aed072f	Riego y Sistemas de Agua	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
17509d85-7af0-451b-9da8-5879b261d639	Estructuras para Exterior	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
6773515e-cbd0-45aa-b803-9a1652121f07	Decoración Exterior	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
01208a12-aaf8-48ae-925f-e65404d3dbe5	Cercas y Vallas	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
e7184f98-a8d4-4a14-85b1-ba31b3a79d3b	Equipos de Mantenimiento Exterior	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
e23041c4-c74b-46ef-a156-3e2bba76bedc	Huerto Urbano y Cultivo Ecológico	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
9ab588e0-33b0-4aee-a585-8ccf13c27d1b	Compostaje y Gestión de Residuos	ad4f2bcf-5d17-424a-883c-d18811e71618	1	t
59567c06-b82d-45f3-925d-631da57913f4	Herramientas y Construcción	\N	0	t
29749a9a-7489-41d8-97b0-cb0071ef3839	Herramientas Eléctricas	59567c06-b82d-45f3-925d-631da57913f4	1	t
51871b1e-760c-4e3a-89e4-6e72fbfdf884	Herramientas Manuales	59567c06-b82d-45f3-925d-631da57913f4	1	t
f798d85f-753f-4607-90b6-0f03fa2e51d5	Pinturas y Tratamientos	59567c06-b82d-45f3-925d-631da57913f4	1	t
2a0c8085-5eac-46d4-bcc0-001bfe95ca28	Materiales de Construcción	59567c06-b82d-45f3-925d-631da57913f4	1	t
19b6d73a-2ab1-405b-90c9-7c112b6dee8e	Fontanería	59567c06-b82d-45f3-925d-631da57913f4	1	t
05ed46fd-b9ac-448b-b678-811bd4ac9200	Electricidad	59567c06-b82d-45f3-925d-631da57913f4	1	t
a923c4a0-aa81-4542-854d-06d47abeb43f	Calefacción y Ventilación	59567c06-b82d-45f3-925d-631da57913f4	1	t
9170c8f8-2501-466d-abbd-c0146d542a9b	Carpintería	59567c06-b82d-45f3-925d-631da57913f4	1	t
429b42fd-b34a-4d77-912b-11d3156cddd3	Equipos de Seguridad Laboral	59567c06-b82d-45f3-925d-631da57913f4	1	t
33864718-2c86-4c99-ae85-7e08a2667c83	Escaleras y Andamios	59567c06-b82d-45f3-925d-631da57913f4	1	t
b2726ed9-ac92-4be1-8a4b-a5f1d443a26b	Materiales de Construcción Sostenibles	59567c06-b82d-45f3-925d-631da57913f4	1	t
5fbea764-1353-4a44-b476-31fc59f58199	Herramientas de Bajo Impacto Ambiental	59567c06-b82d-45f3-925d-631da57913f4	1	t
f13fb12b-5bb8-410b-99a9-e6b56673d7b7	Vehículos y Accesorios	\N	0	t
2a651f57-47b6-403a-9af3-8bce841f5253	Automóviles Nuevos	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
4a87c054-d950-4537-a21e-e12cfbf5301b	Automóviles Usados	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
2ad30c4b-671a-4774-8300-50dc62fc9998	Motos	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
0d12a733-d12f-404c-b307-5c3eb1ed35dd	Repuestos y Recambios	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
e7ae2bcd-e53b-4c6c-a152-f6f549d908b9	Accesorios para Vehículos	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
3328d4cc-91d0-4fcd-8e18-ad6f84e7ebb6	Neumáticos y Llantas	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
bfc141e9-3dd9-47bb-97f8-402430523186	Electrónica para Vehículos	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
78516e49-f872-4454-98e4-bc4a2531c022	Mantenimiento y Cuidado	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
d0ad461b-a82d-4c38-ab1f-c142a236d328	Caravanas y Autocaravanas	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
f993f7de-2c39-4d94-842f-cfcddc5183c0	Bicicletas y Ciclismo	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
9341591e-5993-4a37-9e77-4bb71d687594	Vehículos Eléctricos y Sostenibles	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
0059eea9-5810-48ba-990d-7b218d174f41	Movilidad Sostenible	f13fb12b-5bb8-410b-99a9-e6b56673d7b7	1	t
1218a95b-f894-4d09-9601-c50fc3c9f9be	Deportes y Aire Libre	\N	0	t
4cf65423-70df-4708-b736-48d72adcaa62	Fitness y Musculación	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
7f3dc564-b0b9-489b-850a-d26d0600ea79	Running y Atletismo	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
3f38b5f6-3c38-4124-81ba-eb7991230557	Ciclismo	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
0b95e0e8-180a-43d4-b619-610838e4eac4	Deportes de Equipo	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
d6662473-a8e2-40e2-9840-aea6bf603f92	Deportes Acuáticos	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
19aee94b-6ef1-46f4-b3ef-538a2a7e82f0	Camping y Montaña	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
b765043a-28e5-4f6c-abf2-6510fcae16e0	Caza y Pesca	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
b2cf149e-d961-4f2b-a8d6-aa045a664c18	Esquí y Deportes de Invierno	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
c936e947-dd67-4623-8def-f5b81bb882b4	Nutrición Deportiva	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
a1aa0add-07e5-410a-b0cb-79cac7ff720d	Ropa y Calzado Deportivo	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
d62b2d4e-bd30-4aa3-9a93-10bff5d389e0	Equipamiento Deportivo Sostenible	1218a95b-f894-4d09-9601-c50fc3c9f9be	1	t
f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	Juguetes y Juegos	\N	0	t
89cfab9b-4180-41c5-b5ba-cb6934ea24e6	Juguetes para Bebés e Infantil	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
a1d60a91-c413-438b-9898-dde0c3c5d9a9	Figuras de Acción y Muñecas	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
a95fe34b-ecc8-403c-8118-3c64fb5dd784	Juegos de Mesa y Cartas	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
43a8534b-b5b0-45ae-a356-326bc59244f2	Juegos Educativos	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
02a61f28-4531-44e4-9f54-cf115a682b29	Construcción y Bloques	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
4c2870f6-b943-426c-8de3-d67e8fc0c8ec	Juguetes Electrónicos	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
0d401343-f1a7-4112-8218-c2067bbb54bf	Peluches y Muñecos	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
9ccf9d2c-2890-4c89-b657-9949131855d1	Juegos al Aire Libre	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
748d902c-8af2-49e0-9bee-4b5442d56507	Disfraces y Juego Simbólico	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
b2cad535-1d72-4248-a735-b7a93a042a34	Juguetes Coleccionables	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
49d2e07c-b400-4c74-86fe-fc242d652737	Juguetes Ecológicos y Sostenibles	f9c6eea5-f9c2-4747-b725-7ec1a9f71f2a	1	t
e23df1c5-45cf-4f60-9e3b-e2e3ace99113	Bebés y Maternidad	\N	0	t
53c94628-f7fb-4707-a548-34f88b2ce61e	Alimentación Infantil	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
feff5625-3f45-4d92-85f9-a8b4662f277e	Pañales y Cambiadores	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
a6cd6e1b-626f-45b2-9cbe-7da02aec250d	Transporte	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
abfc8030-9de4-4a46-bcd5-3fecf2dd953f	Ropa y Calzado para Bebés	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
cebe99c5-a45e-4845-b3cb-a8b4cdc61f2a	Dormitorio de Bebé	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
3c93acfe-f49c-4934-b014-3fb879700952	Juguetes para Bebés	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
404e6f9f-4612-4109-9b84-deaf0ef1000d	Higiene y Cuidado del Bebé	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
f02d85bb-5bab-44fb-92b0-a2107bf69345	Lactancia y Alimentación	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
2d375704-ba59-48ee-a167-1ca3ba4144f6	Seguridad Infantil	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
1c426093-b690-4ada-aa66-6e4611d0ad2a	Embarazo y Maternidad	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
6c9296c6-9790-4b1d-931e-4a99616b8a92	Productos Ecológicos para Bebés	e23df1c5-45cf-4f60-9e3b-e2e3ace99113	1	t
91f6a67a-4f51-4e4e-8749-1cbb19c13120	Mascotas	\N	0	t
38ca6e6a-a517-44f0-b054-d252999344ce	Alimentación para Perros	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
ad4959fa-dbf0-41a7-b3a4-594719739445	Alimentación para Gatos	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
01af5b89-b061-404b-93dc-2ebfeb0c0647	Accesorios para Mascotas	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
4fa685c0-696f-4f0a-a250-50984810e5ef	Juguetes para Mascotas	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
c148b225-0fac-41db-b917-6471ee5b24ee	Higiene y Salud Animal	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
dbce1aed-2d0a-47de-b77f-c962690e234a	Camas y Mobiliario	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
98968926-604a-4d1d-8e82-607f20da362a	Jaulas y Transportines	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
4c288928-3019-42eb-b556-689c36bb1f69	Acuarios y Terrarios	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
94f8753b-b169-49ad-8c8b-db407fd19f62	Mascotas Pequeñas y Roedores	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
6fa762fe-49e2-4c81-b043-34e121b10462	Artículos para Aves	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
76e9db38-4e71-47a9-82dd-ffecc30d46da	Productos Ecológicos para Mascotas	91f6a67a-4f51-4e4e-8749-1cbb19c13120	1	t
5a7dcf50-62e2-4489-88e2-e37c62f730cc	Libros y Educación	\N	0	t
89b80805-f1a9-465e-9a83-f5d378d0c3ca	Literatura y Ficción	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
a95aefd9-6b6f-4126-ba59-69cc0fe60483	No Ficción y Ensayo	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
cf2ae4ef-e0a1-4821-b1c7-1182fee23772	Libros Infantiles y Juveniles	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
1942a363-aa7a-46a8-8a28-6e4846f7a12d	Libros de Texto	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
35b1cb2f-57f6-49d8-bf14-6b3785eddc7c	Material Didáctico	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
fe119a29-d5d4-4636-894d-f912a96ed768	Material Escolar	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
5932a93e-2782-46c2-9be3-f3d57dd81402	Cursos y Formación	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
7b49c849-8c07-4e3c-a31b-e49d24f68f87	Libros Digitales y Audiolibros	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
fb80b207-fbaf-459e-90d6-a62a853fa812	Libros Especializados	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
cfeb88cb-67b7-4fca-9e6f-0783b5b70e12	Revistas y Publicaciones	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
59b7de24-6a4c-4dc5-ae6a-dc228b83f3f0	Libros sobre Sostenibilidad y Ecología	5a7dcf50-62e2-4489-88e2-e37c62f730cc	1	t
6a559b24-5260-49df-b726-5260105afa7a	Música y Arte	\N	0	t
0b10f078-85c8-4886-80ce-2e67aeca26bf	Instrumentos de Cuerda	6a559b24-5260-49df-b726-5260105afa7a	1	t
f585b66b-2faa-4a24-b902-4f19c5e6c183	Instrumentos de Viento	6a559b24-5260-49df-b726-5260105afa7a	1	t
789423d4-514e-436c-b458-3f03326bef81	Instrumentos de Percusión	6a559b24-5260-49df-b726-5260105afa7a	1	t
e4233deb-40d4-4ea0-8c8e-c1d3203c6c6b	Equipos de DJ y Producción	6a559b24-5260-49df-b726-5260105afa7a	1	t
d88bf4f4-da19-4be4-948f-08252b44ae03	Accesorios Musicales	6a559b24-5260-49df-b726-5260105afa7a	1	t
bbb67e96-9360-40dc-8e6e-22f4e5c56931	Pintura y Dibujo	6a559b24-5260-49df-b726-5260105afa7a	1	t
d897c6b2-84fc-494b-abf5-4c498d1be19c	Manualidades	6a559b24-5260-49df-b726-5260105afa7a	1	t
8021b31a-5e59-40cd-8ac8-e6dfa6ed341c	Materiales para Bellas Artes	6a559b24-5260-49df-b726-5260105afa7a	1	t
d22f513d-5639-46dc-b1bb-c626e31d45d6	Música Grabada	6a559b24-5260-49df-b726-5260105afa7a	1	t
75b95219-0d43-46b8-815c-69c02640ca4d	Partituras y Libros de Música	6a559b24-5260-49df-b726-5260105afa7a	1	t
67166cda-ec1e-49c4-9ef6-9756e3b4f2a6	Materiales Artísticos Sostenibles	6a559b24-5260-49df-b726-5260105afa7a	1	t
db477c83-ef37-486e-86c3-1b7c5fcd774e	Cine y Series	\N	0	t
7fd3909b-1414-44c0-a5a0-eef00b293b0f	Películas en DVD y Blu-ray	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
2a549030-0ed2-4249-815d-10022dc493b8	Series de TV	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
02ded080-08c4-460b-8362-136a9208d020	Colecciones y Ediciones Especiales	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
02c433b7-ca16-4e95-af33-dd01febdb177	Documentales	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
4bceca3d-69e0-4a7c-b5d2-89450e8b62fe	Animación y Anime	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
a9f3045b-7bf7-41ad-adb4-fb148628fe99	Cine Clásico	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
1de80d39-b9a9-42d1-a787-355c2b1cdacd	Contenido por Streaming	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
25b226a4-2661-4f3b-83b7-ee8ec3819913	Merchandising de Cine	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
410858ca-706a-4acd-a0af-e698ac9273da	Equipamiento para Cinéfilos	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
aeae70a8-23ef-4249-a3c7-832503d3161d	Bandas Sonoras	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
e5051dfb-8f71-4449-b810-8c3cdc42e2bd	Documentales sobre Medioambiente y Sostenibilidad	db477c83-ef37-486e-86c3-1b7c5fcd774e	1	t
122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	Papelería y Artículos de Oficina	\N	0	t
0ca0e751-2fe5-451b-9f36-28aa13030f2c	Escritura	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
b8b12bd4-0a8f-42e5-a233-c5768d41ffcc	Cuadernos y Libretas	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
082e6ead-2bf8-4d39-83e4-3e0f36f127f1	Organización y Archivo	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
3d621aa4-20ed-45ef-868a-fbfdd5a6acc1	Material de Oficina	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
7e154965-92ea-422e-9405-f7f9c1d6bdb3	Papel y Consumibles	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
0fdeba77-aed2-47f6-91e6-5dccee89e222	Mobiliario de Oficina	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
dddf2104-1c51-4817-8921-b82a1e2c0416	Equipos de Presentación	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
ffb5153e-e455-4764-b4c6-04edd29d9790	Planificación y Agendas	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
529694e8-c4e5-4377-8a94-20eb5797e780	Sellos y Productos de Timbrado	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
69788b46-b0e1-47d5-b32d-08eceec4b601	Arte y Manualidades de Oficina	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
70d24e3f-12da-4749-9b7f-0ff1f9e08323	Papelería Sostenible y Reciclada	122beeb1-6a71-4dfd-861c-ee4af3a0fa8c	1	t
25255cc3-7620-40f0-8de4-0bce8469b759	Equipamiento Profesional e Industrial	\N	0	t
bad07068-fe75-4041-a8a5-bff282c38658	Maquinaria Industrial	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
3d55b4b7-7f54-449f-a7a9-57d82041dadb	Herramientas Profesionales	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
5b561f59-74ff-4f90-ab87-df8b4210992d	Equipos de Medición y Precisión	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
f7c7db8c-2332-45ec-b95f-7d450e6f1035	Suministros Industriales	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
47ed33a0-a9f6-4d38-99b1-67b7c355b6fd	Equipamiento para Hostelería	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
ba3e279e-f43b-40cc-869b-8d3d67d002e1	Equipo Médico Profesional	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
dcbbaa98-71d7-489c-b9be-ebe85f98ad22	Material para Laboratorio	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
ebb88ec7-ce15-4eb2-bb23-94d884af153d	Equipamiento para Comercios	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
3f6af91a-cb31-469c-98e5-cdb02d8fe961	Vestuario y Seguridad Laboral	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
0da61a0b-3451-4607-b9b8-baf7fd768ccb	Almacenaje Industrial	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
8a04b2f9-dec4-4db7-b16d-3f8da569ac32	Equipamiento Industrial Energéticamente Eficiente	25255cc3-7620-40f0-8de4-0bce8469b759	1	t
2a780a6e-36d7-4754-9d42-461327a485f4	Productos de Limpieza	\N	0	t
cf6a8fa2-5510-47e9-882f-40d0900cb7c8	Limpiadores Multiusos	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
8494dc52-9b7d-4d45-b16e-f8da7905051f	Productos para Cocina	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
914cd2fd-62b8-4962-b450-37c83b0c7690	Productos para Baño	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
2c1d2d79-f4e2-4fc8-85f6-aa0caecd7734	Limpieza de Suelos	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
f163d972-378f-4f5e-8ed8-127c5721bdf0	Lavandería	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
e76a362b-338a-46a8-948b-b293a585c97f	Ambientadores y Fragancias	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
db17c96c-5a47-4166-8ca5-6b69a8fe8390	Útiles de Limpieza	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
0a74cfde-bd59-4cc7-ae81-b67a0af109a6	Productos Ecológicos de Limpieza	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
cdb26a4b-acfe-43aa-8e18-550c208b72f8	Limpiadores Específicos	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
efff7fe6-326e-44ee-9f98-9a768e2f17c1	Productos Profesionales	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
267a8070-7711-48c3-9b41-4f89c751e029	Productos de Limpieza Biodegradables	2a780a6e-36d7-4754-9d42-461327a485f4	1	t
27db6554-daff-41f2-b635-cec2009f2bda	Software y Servicios Digitales	\N	0	t
34d9c9da-650c-40d3-831e-2ad948b1d041	Sistemas Operativos	27db6554-daff-41f2-b635-cec2009f2bda	1	t
5c357ee2-e39b-451a-94bd-51660e637ac4	Software de Oficina	27db6554-daff-41f2-b635-cec2009f2bda	1	t
c58310f4-397c-4aba-85b9-36bad3acd262	Software de Diseño y Creatividad	27db6554-daff-41f2-b635-cec2009f2bda	1	t
2707b7c3-a30e-420f-ba47-532d845c49f1	Antivirus y Seguridad	27db6554-daff-41f2-b635-cec2009f2bda	1	t
7a42d481-af82-4ee1-826a-30ced31fb8fc	Software Educativo	27db6554-daff-41f2-b635-cec2009f2bda	1	t
d6ec8064-cb40-4cb5-980b-1c3622f38d30	Aplicaciones Móviles	27db6554-daff-41f2-b635-cec2009f2bda	1	t
9e77749a-5065-4132-8e72-eed5a47b4e25	Suscripciones Digitales	27db6554-daff-41f2-b635-cec2009f2bda	1	t
71c07be8-f49f-44f4-bfc0-f37551a40a1c	Almacenamiento en la Nube	27db6554-daff-41f2-b635-cec2009f2bda	1	t
bb6f015d-1ee1-4520-a081-8d1a9cfbb9f5	Software Empresarial	27db6554-daff-41f2-b635-cec2009f2bda	1	t
2046a4bb-7824-4d30-8c61-ae9997723e03	Juegos Digitales	27db6554-daff-41f2-b635-cec2009f2bda	1	t
ca52c251-a233-4f54-af5e-0c02a0e59aa4	Software para Gestión Ambiental	27db6554-daff-41f2-b635-cec2009f2bda	1	t
bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	Viajes, Turismo y Equipaje	\N	0	t
b7019af7-4fad-4dce-99d2-4710efc0807a	Maletas y Trolleys	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
68f022c1-e3b6-4194-b80a-ac486d57c526	Mochilas y Bolsas de Viaje	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
9860af62-2adf-4cf5-8ebe-ca7cb1938427	Accesorios de Viaje	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
1e28d974-095b-428c-86a9-427ed8365c67	Paquetes Turísticos	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
8ca413ad-8259-4040-9f09-58edc5fa1e0e	Escapadas y Experiencias	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
3d9aa3f8-89d2-4b39-957d-2a0f68399c1d	Hoteles y Alojamiento	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
ad4a75c2-d381-401e-8667-b0b2a8abdf42	Vuelos y Transporte	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
51e62bdd-01c6-4609-8d2e-827d16c21f6c	Guías de Viaje	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
1fa756fb-a859-4003-819a-55513fdeaaa8	Material de Camping	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
b66510fc-a048-438b-a985-0f3771429560	Actividades Turísticas	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
6932f323-095e-49ad-a1d3-b33a94d7d193	Ecoturismo y Turismo Sostenible	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
112790f9-1ed9-43e6-9645-7b145a051317	Equipaje Sostenible	bc9a4f71-1d08-4747-83f2-09b2dcc84c3e	1	t
e8a83854-caed-4706-98e2-0d91653a36d0	Fiestas y Eventos	\N	0	t
f4be8ede-5967-4a35-b441-6189e704818b	Artículos para Fiestas	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
3151c8bd-12e0-48d4-9eb0-5041ef1eaa2c	Decoración de Eventos	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
922bb5e9-246d-477c-a0c2-90ccb6a2ea8e	Disfraces y Complementos	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
07706f01-b5d7-4bda-8b14-0d13c9a3589c	Artículos para Bodas	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
7037627c-776a-479d-bacb-901ca53bb561	Artículos para Cumpleaños	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
d61e7bbb-53d6-4224-b635-e1aebf3a6fb4	Artículos para Festividades	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
11eb4aa7-6ee9-4aec-9043-661bc08bbb7d	Papelería de Fiesta	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
7cd48696-c009-47e0-8342-a7877262338a	Regalos y Recuerdos	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
064eb6b9-39b7-4ebd-a320-be699cc110d4	Piñatas y Juegos	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
31a5dc60-9817-4f58-a7cf-d1500b3a0fd6	Artículos para Catering	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
61c1f325-d649-4dd4-b1f8-09f38b0ccfec	Artículos para Eventos Sostenibles	e8a83854-caed-4706-98e2-0d91653a36d0	1	t
2cb29704-d0ba-4acf-bee4-c1c253f6cb94	Coleccionables y Antigüedades	\N	0	t
e07d4af2-0f8c-4b00-8f2b-cf11f3fb7047	Monedas y Billetes	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
e9a155cf-4685-40d4-a24b-028c9749baac	Sellos	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
9b80a848-1c41-4945-9b0e-5d1bbf4c11e8	Cómics y Libros Raros	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
a10e59f9-f995-4d8d-a402-39feaf350d8e	Figuras Coleccionables	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
1c73d33b-5bea-43b1-bcaf-23d6e1d50965	Antigüedades	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
8accd7eb-6987-4946-9345-81c0823c7d70	Arte y Obras de Colección	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
90d805f7-2ce0-474f-a112-ddb747616ccc	Memorabilia Deportiva	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
02e6a160-7448-4f98-b496-c30d1c5a0342	Tarjetas Coleccionables	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
4d26440c-cac7-4f5f-8ac0-ff5ab8ce1ba0	Vinilos y Música de Colección	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
dae7d6ab-7319-4b1b-bf50-74d4d8c600ff	Objetos Vintage	2cb29704-d0ba-4acf-bee4-c1c253f6cb94	1	t
315c5b1f-0e2d-435a-b0fa-b278de36b60a	Productos Culturales y Ceremoniales	\N	0	t
ae0bf662-b644-4d22-8632-1ce02fa69db4	Artículos Religiosos	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
aba369ed-c1d8-4d87-8ba6-aea6ce63b0cb	Ceremonias y Rituales	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
0dfd315c-1427-4e3b-b55d-2f96abfcd37c	Artesanía Tradicional	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
607b83bd-7860-4bd3-b36a-dcb881eb91a2	Productos Regionales	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
30d64ba8-42ff-4e50-955d-e056def15856	Souvenirs y Recuerdos	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
c39a3139-5e86-4770-975d-a2cc2f593b9a	Decoración Étnica	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
3432884d-9b69-4979-bfec-2162500a719b	Textiles Tradicionales	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
ba58f452-c03c-4a8d-864c-845975801ccc	Gastronomía Cultural	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
bd2cdd9a-e7f3-4faf-8e66-4882af685f1f	Productos Festivos	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
2914c6b1-7490-48a7-8ff2-e926d077fbfe	Patrimonio Cultural	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
66ceca12-cf06-41ba-87df-4087d1cf6bba	Artesanía Sostenible y Comercio Justo	315c5b1f-0e2d-435a-b0fa-b278de36b60a	1	t
0178a113-0ff5-426e-9634-3901f5b91142	Productos para Adultos	\N	0	t
d5d1bc10-25f9-4527-b314-147a5813996d	Lencería y Ropa Íntima	0178a113-0ff5-426e-9634-3901f5b91142	1	t
b08113e1-4329-4212-8fb6-e780a9ca36a0	Juguetes para Adultos	0178a113-0ff5-426e-9634-3901f5b91142	1	t
0cf4e33c-44a3-4e53-ac9f-5c113794a889	Salud Sexual	0178a113-0ff5-426e-9634-3901f5b91142	1	t
7653cfa1-c1b6-4953-b78b-805043207b3e	Libros y Revistas para Adultos	0178a113-0ff5-426e-9634-3901f5b91142	1	t
131a98c1-c1fb-4fef-8834-8070266907ee	Artículos para Despedidas	0178a113-0ff5-426e-9634-3901f5b91142	1	t
dede9480-c101-43cf-bbb6-57210209dce3	Juegos para Adultos	0178a113-0ff5-426e-9634-3901f5b91142	1	t
64943613-ea0e-4113-927e-fe2dd1d96083	Bienestar Íntimo	0178a113-0ff5-426e-9634-3901f5b91142	1	t
749af9ea-2c04-4795-bbc4-92a85ffaa712	Accesorios Temáticos	0178a113-0ff5-426e-9634-3901f5b91142	1	t
dfea54b0-07b1-4641-8011-ec2cc2185d16	Cosmética Especializada	0178a113-0ff5-426e-9634-3901f5b91142	1	t
be892b34-d181-4ce8-abed-d4f1f7a52178	Contenido Digital para Adultos	0178a113-0ff5-426e-9634-3901f5b91142	1	t
576bc743-485b-46ac-8ba4-7452aa4e7cc1	Productos Íntimos Ecológicos	0178a113-0ff5-426e-9634-3901f5b91142	1	t
a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	Seguridad y Vigilancia	\N	0	t
955601a6-91b4-4b39-8ca5-a49da8b4176c	Alarmas y Sistemas de Seguridad	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
99996e21-c408-4af5-9f6c-8241cdb05768	Cámaras de Vigilancia	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
26dc5eb0-0479-493c-a4a7-971dfdcc98fa	Cerraduras y Control de Acceso	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
d249ba45-dda9-488a-84b1-e34dc0ce5525	Cajas Fuertes	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
bb1a6663-052a-494d-b2b6-91ba443e0992	Seguridad Informática	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
f21f517e-165e-41e8-86b5-a5cf938353a2	Protección Personal	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
2fe38c87-a0bc-40ef-9fd6-2a2d21f88c06	Seguridad Familiar	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
639ac018-b344-4c2e-b457-8aa5989c7d8b	Seguridad Vehicular	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
7f41cb32-4baa-4131-a8b3-9625fc1ef3b0	Seguridad en el Trabajo	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
96fcfb9d-bb54-4114-82a9-6cdb57925291	Iluminación de Seguridad	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
d21e719f-ae8d-4b22-a19a-29da07b4ba8a	Sistemas de Seguridad de Bajo Consumo	a1d8cb91-d1b3-4628-ad48-dd2d5fc49998	1	t
b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	Energía y Climatización	\N	0	t
b42a01c9-b989-49e8-95b1-c28ddb9e9355	Aires Acondicionados	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
00bce76d-0ef1-4f86-8ef4-c72a1abbe36f	Calefacción	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
b686e411-770d-4ec9-9f82-8a97958775dd	Ventilación	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
0624481f-e224-4686-b845-3b1f8e44ebd9	Energía Solar	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
e2a3e4c4-9381-4745-9423-214a56851b52	Generadores	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
1fafc6a5-9d3c-46b1-afdc-d21fcb3af11b	Estufas y Chimeneas	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
781e6b2d-7ef0-4ae2-aeec-fe761b32b7f5	Bombas de Calor	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
939dc88b-5189-427f-9f24-7c6fd64e7433	Termostatos Inteligentes	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
aa492780-126b-499f-b9a7-a1332fb89faf	Aislamiento Térmico	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
d2296a68-f5da-45cc-a78d-a3a400163a57	Climatización para Negocios	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
c6e41c78-a1e5-4be9-a4df-285d8aecc2c6	Soluciones de Energías Renovables	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
3f2b827a-31dc-4485-9c5d-10e8dd343cde	Equipos de Eficiencia Energética	b44c4ac0-ce0c-4d2d-a620-fc2e98c86fab	1	t
\.


--
-- Data for Name: cuotas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cuotas (id, servicio_id, nombre, limite_uso, plan_stripe, activo) FROM stdin;
'e0812056-3177-4e21-baa1-8265cb717220'	'e459c774-2faf-498a-b3e3-5bf21177d16e'	'TICKET_PROCESSING_QUOTA'	500	'price_1Qt6IdKPUVcoxoHV7bhutvwL'	t
'9b9393dd-4d86-44f2-8514-1e317cfa955b'	'0bb1bef2-061f-4bbb-86ae-0d59424483cb'	'MODIFY_TICKET_QUOTA'	3000	'price_1Qt6IdKPUVcoxoHV7bhutvwL'	t
'e1a47137-60ba-47b3-86b5-3d9826779ef2'	'360ac6a4-ac5e-4034-9195-a2f660e5c1a4'	'CREATE_TICKET_QUOTA'	1000	'price_1Qt6IdKPUVcoxoHV7bhutvwL'	t
\.


--
-- Data for Name: items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.items (id, receipt_id, nombre, precio, cantidad, categoria_id, sub_categoria_id) FROM stdin;
ee28e673-5588-41eb-9ed8-1194840461d3	15582a11-1d21-410a-87e5-801ea40c66e9	GOURMET MAXI	6.50	1	\N	\N
9e194831-0c38-4b5c-af5d-087f0bca95ea	15582a11-1d21-410a-87e5-801ea40c66e9	BICARBONATO KILO	0.90	1	\N	\N
c523737f-6b16-42cb-b470-ca3fb33acbe6	15582a11-1d21-410a-87e5-801ea40c66e9	VINAGRE LIMPIEZA	2.55	1	\N	\N
a90f2435-53ef-46c9-84f4-141941e2f298	15582a11-1d21-410a-87e5-801ea40c66e9	MASCARPONE	1.50	1	\N	\N
5dda4af3-f2ce-4efe-98f9-f81656ba151a	15582a11-1d21-410a-87e5-801ea40c66e9	UNTAR SUAVE	2.45	1	\N	\N
eed0eff3-6a2e-4907-8b87-e3a6af054dc1	15582a11-1d21-410a-87e5-801ea40c66e9	JUESO GOUDA LONCHAS	3.95	1	\N	\N
76562416-22ed-49bf-b10c-43becd7abf51	15582a11-1d21-410a-87e5-801ea40c66e9	GUACAMOLE 500 GR	2.50	1	\N	\N
96f0b995-e450-4bdc-bb40-ad3c6b136b09	15582a11-1d21-410a-87e5-801ea40c66e9	TRONOPIO SURIMI	2.20	1	\N	\N
a46d5715-06f8-4102-ad13-34490a37cc39	15582a11-1d21-410a-87e5-801ea40c66e9	NATA MONTAR	1.40	1	\N	\N
fc608d2c-fcc5-4ab0-8ea4-dd0f854dfa55	0c199fb2-539e-4fe6-92fd-8e22620c5e68	GOURMET MAXI	32.00	1	\N	\N
8831f7a7-a7b0-4245-a307-b24c2eb595f3	0c199fb2-539e-4fe6-92fd-8e22620c5e68	BICARBONATO KILO	0.50	1	\N	\N
1c6015e6-6f2e-4a66-ba42-720c36d59522	0c199fb2-539e-4fe6-92fd-8e22620c5e68	VINAGRE LIMPIEZA	2.55	1	\N	\N
7ec89aeb-a153-4fa9-8b1d-c379acc38d67	0c199fb2-539e-4fe6-92fd-8e22620c5e68	MASCARPONE	1.50	1	\N	\N
17714797-0db8-4725-a78e-91b4e065f53d	0c199fb2-539e-4fe6-92fd-8e22620c5e68	UNTAR SUAVE	2.45	1	\N	\N
8371da01-54a4-4b67-8906-c29dedc5c90f	0c199fb2-539e-4fe6-92fd-8e22620c5e68	LUESO GOUDA LONCHAS	3.95	1	\N	\N
1b4710d1-9ad3-4108-bb57-28e2e681b274	0c199fb2-539e-4fe6-92fd-8e22620c5e68	SUACLE 500 GR	2.50	1	\N	\N
29f76b51-7695-430e-b403-527bca90254d	0c199fb2-539e-4fe6-92fd-8e22620c5e68	TRANG 10 SURIMI	2.20	1	\N	\N
f7f903a0-7331-40bf-bc88-6c8e42f6be27	0c199fb2-539e-4fe6-92fd-8e22620c5e68	NATA MONTAR	1.40	1	\N	\N
d21825c1-ff13-4652-bf94-2368fdc82a81	1c342f02-3073-4993-aa52-d82ac5fae1e0	GOURMET MAXI	60.00	1	\N	\N
f4149956-afa8-4900-ae34-0ff76c9ad68c	1c342f02-3073-4993-aa52-d82ac5fae1e0	BICARBONATO KILO	0.90	1	\N	\N
bf78c0a0-de27-4195-9aaa-504382b7bdf6	1c342f02-3073-4993-aa52-d82ac5fae1e0	VINAGRE LIMPIEZA	2.55	1	\N	\N
1be8bf39-70fc-4426-b6cc-1bfd960d83fa	1c342f02-3073-4993-aa52-d82ac5fae1e0	MASCARPONE	1.50	1	\N	\N
aaed1919-ad1d-4cb2-9e77-7e69f1283f7a	1c342f02-3073-4993-aa52-d82ac5fae1e0	UNTAR SUAVE	2.45	1	\N	\N
dfe99829-6725-41ba-b476-772daef34a74	1c342f02-3073-4993-aa52-d82ac5fae1e0	JUESO GOUDA LONCHAS	3.95	1	\N	\N
ed7b8bf7-c54e-408f-adf0-4b6db17b9ed9	1c342f02-3073-4993-aa52-d82ac5fae1e0	GUACAMOLE 500 GR	2.50	1	\N	\N
d51df4f5-d7f4-4807-be02-8a88f3265d8c	1c342f02-3073-4993-aa52-d82ac5fae1e0	TRONOPIO SURIMI	2.20	1	\N	\N
d1b35c39-0237-47db-92fd-4eb778f17573	1c342f02-3073-4993-aa52-d82ac5fae1e0	NATA MONTAR	1.40	1	\N	\N
37d6d8a3-c20d-4079-80c6-a34b398dc6d0	6524f4a5-29fe-4d23-90fd-786e00ea04c7	GOURMET MAXI	6.50	1	\N	\N
089f5e51-c0a3-4a1e-8b8b-05bc6da402cf	6524f4a5-29fe-4d23-90fd-786e00ea04c7	BICARBONATO KILO	0.90	1	\N	\N
dd03854a-c1d7-47b0-961d-f29519469eb9	6524f4a5-29fe-4d23-90fd-786e00ea04c7	VINAGRE LIMPIEZA	2.55	1	\N	\N
0c0e2eb9-c25d-44d5-a8d0-6e754f35cd0d	6524f4a5-29fe-4d23-90fd-786e00ea04c7	MASCARPONE	1.50	1	\N	\N
a887d0d0-9d61-46c0-b283-65631d81d2d1	6524f4a5-29fe-4d23-90fd-786e00ea04c7	UNTAR SUAVE	2.45	1	\N	\N
5fac030e-dc70-48ea-b489-da4f688e05fc	6524f4a5-29fe-4d23-90fd-786e00ea04c7	JUESO GOUDA LONCHAS	3.95	1	\N	\N
dfb542cf-a800-40d9-8f9c-7f16f820e755	6524f4a5-29fe-4d23-90fd-786e00ea04c7	GUACAMOLE 500 GR	2.50	1	\N	\N
c1c43e38-d692-4a37-aabf-3e59e9779906	6524f4a5-29fe-4d23-90fd-786e00ea04c7	TRONOPIO SURIMI	2.20	1	\N	\N
ee39a5c4-9cb4-4b5a-8cd4-77b8c0fdce95	6524f4a5-29fe-4d23-90fd-786e00ea04c7	NATA MONTAR	1.40	1	\N	\N
6ce48ea4-f2c6-4fae-b645-c52a72573a93	2ba40977-c476-4f69-b33e-759d5a4c906e	MBINADO APERITIVO	3.10	1	\N	\N
a9fcd6a9-6d9d-43c0-a1af-1281a7097bae	2ba40977-c476-4f69-b33e-759d5a4c906e	ARS MANTEQUILLA	0.80	1	\N	\N
0fe2f214-a5e7-4e44-bf4d-7a17fe0d8522	2ba40977-c476-4f69-b33e-759d5a4c906e	TIRAS FRITAS	5.70	1	\N	\N
cbcdffd8-ac28-4f63-91a7-4dff09b29b7e	2ba40977-c476-4f69-b33e-759d5a4c906e	LS PATATA GRANDE	0.75	1	\N	\N
d4125e18-0f9d-4517-bb68-8a43f0a0c58a	2ba40977-c476-4f69-b33e-759d5a4c906e	MANTEL ROLLO COLORES	4.75	1	\N	\N
ef06b75a-2a6d-4313-8c71-f030a3abf8fb	2ba40977-c476-4f69-b33e-759d5a4c906e	CROISSANT CACAO	2.90	2	\N	\N
3c71bbd2-b074-4d02-9fd7-72319e02157b	2ba40977-c476-4f69-b33e-759d5a4c906e	MERLUZA REBOZADA	3.40	2	\N	\N
98523f5a-661c-4f39-ae85-9eb7e669e9a8	2ba40977-c476-4f69-b33e-759d5a4c906e	HILO DENTAL PACK-2	7.50	1	\N	\N
898be3b8-e909-4593-a91d-53e065a9db70	2ba40977-c476-4f69-b33e-759d5a4c906e	MINI CARITA CACAO	1.80	1	\N	\N
20d9d02a-8bce-4350-9ccd-3b5a6dca7bf8	2ba40977-c476-4f69-b33e-759d5a4c906e	PANECILLO 11 UDS	1.40	1	\N	\N
2f0a33c6-439a-44e0-9e21-89edab5e314d	2ba40977-c476-4f69-b33e-759d5a4c906e	PIZZA JAMON Y QUESO	1.14	1	\N	\N
294054c6-d4e0-4580-a958-5a9f8106aa1a	2ba40977-c476-4f69-b33e-759d5a4c906e	MAGDALENA AZUCAR	2.50	1	\N	\N
d1243e80-494c-4997-900e-eeb54b6f7364	2ba40977-c476-4f69-b33e-759d5a4c906e	QUESO LONCHAS TIERNO	2.60	1	\N	\N
aa9b5c8b-615a-425e-9255-998568b6a95a	2ba40977-c476-4f69-b33e-759d5a4c906e	NEVAL 6L	2.24	2	\N	\N
0be5f30f-0b3f-4bf2-8fda-622df844eb7b	2ba40977-c476-4f69-b33e-759d5a4c906e	AZUCAR MORENO PANELA	1.62	1	\N	\N
ec97ce84-9380-49d1-897b-7e29f4784b28	2ba40977-c476-4f69-b33e-759d5a4c906e	NARANJA	2.05	2	\N	\N
1c8771c7-eec2-4890-8731-fcf6ed064d93	2ba40977-c476-4f69-b33e-759d5a4c906e	COLA 2 L	3.70	1	\N	\N
3210135f-931d-4007-93bc-a4a891d18ed4	2ba40977-c476-4f69-b33e-759d5a4c906e	CC ZERO ZERO 2L	2.10	2	\N	\N
1ceab415-b5f3-44ea-a953-3039f9139b6c	2ba40977-c476-4f69-b33e-759d5a4c906e	PIZZA POLLO	4.20	1	\N	\N
d4dfc1a7-7045-4f1c-a423-b703a75677e4	2ba40977-c476-4f69-b33e-759d5a4c906e	TORTILLA PAT C/CEB	2.90	3	\N	\N
7955445f-7dcb-4e0f-8109-51ff97e819f2	2ba40977-c476-4f69-b33e-759d5a4c906e	TARTA UNICORNIO	7.80	1	\N	\N
8d557b8f-93ad-432e-86c8-dc35c8fbfae6	2ba40977-c476-4f69-b33e-759d5a4c906e	12 HUEVOS GRANDES	13.80	1	\N	\N
9cb338e3-3dc2-419b-af83-b5c0135841a6	2ba40977-c476-4f69-b33e-759d5a4c906e	NUGGETS DE POLLO	2.28	2	\N	\N
84582d61-cd50-4cd9-8cf9-28d37296a3ba	2ba40977-c476-4f69-b33e-759d5a4c906e	LS PAELLA ΜΙΧΤΑ	5.40	2	\N	\N
19137c0c-4e58-4f43-9807-0ddff0fd9e31	2ba40977-c476-4f69-b33e-759d5a4c906e	LCASEI FRESA X 12	9.00	1	\N	\N
309da95d-dac5-40f3-b725-a44e047b19eb	2ba40977-c476-4f69-b33e-759d5a4c906e	ACEITUNA R/ANCHOA P3	2.22	1	\N	\N
79a4bffc-7e83-4886-a7bd-16f49ca024dc	2ba40977-c476-4f69-b33e-759d5a4c906e	ENSALADILLA RUSA	2.91	1	\N	\N
ae18397e-e924-418b-830d-53b46f6744c2	2ba40977-c476-4f69-b33e-759d5a4c906e	CAPRICHOS JAMÓN	3.00	1	\N	\N
0fdf9a20-418b-4bdf-af97-7fe3a9e4bf18	2ba40977-c476-4f69-b33e-759d5a4c906e	PIZZA BARBACOA/BACON	2.00	1	\N	\N
94ecd977-952c-4858-bb80-3c27e4af1a62	2ba40977-c476-4f69-b33e-759d5a4c906e	PIZZA JAMON/QUESO	3.40	2	\N	\N
c09bc77e-93fd-4e71-8f91-769a79547adc	2ba40977-c476-4f69-b33e-759d5a4c906e	BANANA	3.30	1	\N	\N
dedf8988-354a-40a8-846c-515efefdeb91	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	MBINADO APERITIVO	3.10	1	\N	\N
f8f00e72-47b9-4034-8fba-f8034c9c986c	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	ARS MANTEQUILLA	0.80	1	\N	\N
d60e6bda-1ecd-41ec-99da-6e81c9585fc9	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	AT. CLASSICAS	5.70	1	\N	\N
49dc02f8-2c38-4723-9122-f54dbb2d5111	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	TIRAS FRITAS	0.75	1	\N	\N
5b728e2f-fc5b-4e17-9420-2dc828b88098	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	LS PATATA GRANDE	4.75	1	\N	\N
81d9ace6-3871-4cc4-bfca-fa1c4ce91bbf	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	MANTEL RULLO COLORES	2.90	1	\N	\N
0ef630e3-dc10-4b2b-9b45-90a4003c3e7e	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	CROISSANT CACAO	3.40	2	\N	\N
e2531d09-fbbb-4c9f-904c-5a3c396315ba	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	MERLUZA REBOZADA	7.50	2	\N	\N
1adcc4c3-8d9a-42a0-a1d4-cb5b3f314cc2	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	HILO DENTAL PACK-2	1.80	1	\N	\N
346e418e-96ce-42fe-9a06-7e4f45730931	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	MINI CARITA CACAO	1.40	1	\N	\N
2aecb942-22aa-4da8-bd7a-799443742037	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	PANECILLO 11 UDS	1.14	1	\N	\N
4cb692a9-bd7b-483f-b73b-d21f82166441	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	PIZZA JAMON Y QUESO	2.50	1	\N	\N
3d3beacd-b7e0-4c98-98b6-69f866deceec	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	MAGDALENA AZUCAR	2.60	1	\N	\N
c644d96e-df15-40e7-a5e9-e7fdbcfdfc20	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	QUESO LONCHAS TIERNO	2.24	1	\N	\N
bf3a63fb-8500-4548-8ab0-7808e2eebdbd	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	NEVAL 6L	1.62	2	\N	\N
7d0e6b27-597b-4510-9d82-4dd19c0b2d61	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	AZUCAR MORENO PANELA	2.05	1	\N	\N
f0d766be-6c1c-43d0-b789-e1b95b866098	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	NARANJA	3.70	2	\N	\N
c381a4e6-be88-444f-bd06-8e1a449d7192	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	COLA 2 L.	2.10	1	\N	\N
b7a953c2-7ca9-497b-94d4-a408a2870241	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	CC ZERO ZERO 2L	4.20	2	\N	\N
6c1b7bc2-1553-4fdf-8985-e0621c0e89fd	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	PIZZA POLLO	2.90	1	\N	\N
40cc11a7-5e91-4845-bc5d-68eb2a25512d	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	TORTILLA PAT C/CEB	7.80	3	\N	\N
e33384c6-4f46-4936-bf97-5995bba9ddc9	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	TARTA UNICORNIO	13.80	1	\N	\N
496d0570-5571-44c4-8e39-2b720a31c829	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	12 HUEVOS GRANDES	2.28	1	\N	\N
7fc1c999-05f0-413a-82af-9318cae1a62c	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	NUGGETS DE POLLO	5.40	2	\N	\N
1dd5ad0d-dc10-47bf-a959-c65e86818712	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	LS PAELLA MIXTA	9.00	2	\N	\N
a1951375-e964-4849-baa8-e025926d3e7a	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	LCASEI FRESA X 12	2.22	1	\N	\N
0e91c77b-f2ab-44b5-9acf-8ba10a3e294c	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	ACEITUNA R/ANCHOA P3	2.91	1	\N	\N
cf7c0dd8-3308-42ef-92d2-702a83f6e533	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	ENSALADILLA RUSA	35.00	1	\N	\N
facd1113-e202-49b2-ac38-57a8530576c3	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	CAPRICHOS JAMÓN	3.00	1	\N	\N
efe52aa6-45d3-4045-8672-3d87fd3f8fce	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	PIZZA BARBACOA/BACON	3.00	1	\N	\N
e2f59a84-bccb-4532-a1c2-c4e5f505ffec	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	PIZZA JAMON/QUESO	3.00	2	\N	\N
22386558-890b-4da4-85a8-5b7a942770cf	f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	BANANA	3.00	1	\N	\N
5adf0464-5366-458f-b423-9f907d8f71fe	98a128f2-5d36-4fec-bc70-c48776432ad1	GOURMET MAXI	2.55	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	7ecb0a74-daf9-4a17-973d-ee5fb13d91c2
ba1564ca-bcc1-4188-b592-97cc671e8687	98a128f2-5d36-4fec-bc70-c48776432ad1	BICARBONATO KILO	1.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	41d71736-8e92-491f-af3f-54d4e5f64af1
e649d988-f5e1-4ae7-aa0e-b66567e806fd	98a128f2-5d36-4fec-bc70-c48776432ad1	VINAGRE LIMPIEZA	2.45	1	2a780a6e-36d7-4754-9d42-461327a485f4	cf6a8fa2-5510-47e9-882f-40d0900cb7c8
d60b6401-02c6-4743-98f7-4c568f69587a	98a128f2-5d36-4fec-bc70-c48776432ad1	MASCARPONE	3.95	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
0353dcc7-d5ad-4298-ba6d-716ec4ef7236	98a128f2-5d36-4fec-bc70-c48776432ad1	UNTAR SUAVE	2.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	2d3d4f88-15c0-474e-bac8-816bf4c447cd
a976239e-6d5c-4784-8327-5b15c28f5a33	98a128f2-5d36-4fec-bc70-c48776432ad1	JUESO GOUDA LONCHAS	2.20	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
e8ae838e-b111-40dc-a240-b9a747eb3b55	98a128f2-5d36-4fec-bc70-c48776432ad1	GUACAMOLE 500 GR	1.40	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	70830fd9-d781-426b-8b82-29c5b11772d4
0135a01b-dd08-44da-90c9-dde8324db16c	98a128f2-5d36-4fec-bc70-c48776432ad1	TRONQUITO SURIMI	0.00	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	efaeece6-1aa2-4265-b961-1308cd4aa898
7cfe715e-b307-4aed-874a-88deeefea093	98a128f2-5d36-4fec-bc70-c48776432ad1	NATA MONTAR	0.00	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
9390b77b-ab4d-41f1-baf3-bcf3fe9dd15b	4af2d7c2-32a5-4933-b804-a519fbdbbc21	GOURMET MAXI	6.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	7ecb0a74-daf9-4a17-973d-ee5fb13d91c2
26cee637-41b8-46d5-b104-229f01f29eaa	4af2d7c2-32a5-4933-b804-a519fbdbbc21	BICARBONATO KILO	0.90	1	2a780a6e-36d7-4754-9d42-461327a485f4	8494dc52-9b7d-4d45-b16e-f8da7905051f
72a1db7b-29f1-4b77-b5d2-fb9aeee03ed5	4af2d7c2-32a5-4933-b804-a519fbdbbc21	VINAGRE LIMPIEZA	2.55	1	2a780a6e-36d7-4754-9d42-461327a485f4	cf6a8fa2-5510-47e9-882f-40d0900cb7c8
a0571902-0e16-4497-a122-9b4119dcc290	4af2d7c2-32a5-4933-b804-a519fbdbbc21	MASCARPONE	1.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
a71e763d-11c2-4ad1-b8d1-fab04846f8c1	4af2d7c2-32a5-4933-b804-a519fbdbbc21	UNTAR SUAVE	2.45	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	41d71736-8e92-491f-af3f-54d4e5f64af1
0fe2e57c-fb06-473f-83cf-185005a21a2c	4af2d7c2-32a5-4933-b804-a519fbdbbc21	JUESO GOUDA LONCHAS	3.95	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
321b1ce0-0884-4ce9-8053-0dbd75365840	4af2d7c2-32a5-4933-b804-a519fbdbbc21	GUACAMOLE 500 GR	2.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	70830fd9-d781-426b-8b82-29c5b11772d4
790af966-afc7-4b40-9fb8-efacc5bcd1d3	4af2d7c2-32a5-4933-b804-a519fbdbbc21	TRONOPIO SURIMI	2.20	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	efaeece6-1aa2-4265-b961-1308cd4aa898
51c9c6aa-c0c5-48ce-8ba3-1b64d7f1e290	4af2d7c2-32a5-4933-b804-a519fbdbbc21	NATA MONTAR	1.40	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
863b193f-c934-4cc5-92c4-cc57304c5419	ab64e66d-efc5-47d5-97f3-3a60c962cf36	GOURMET MAXI	6.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	7ecb0a74-daf9-4a17-973d-ee5fb13d91c2
66b5a8b6-70d6-4a8b-9c18-04ae016c9031	ab64e66d-efc5-47d5-97f3-3a60c962cf36	BICARBONATO KILO	0.90	1	2a780a6e-36d7-4754-9d42-461327a485f4	8494dc52-9b7d-4d45-b16e-f8da7905051f
5b22e5b6-2b0c-4610-82d2-264cfc66c628	ab64e66d-efc5-47d5-97f3-3a60c962cf36	VINAGRE LIMPIEZA	2.55	1	2a780a6e-36d7-4754-9d42-461327a485f4	cf6a8fa2-5510-47e9-882f-40d0900cb7c8
bff3adb4-d183-4701-a60c-6aedbd8b11ae	ab64e66d-efc5-47d5-97f3-3a60c962cf36	MASCARPONE	1.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
e175440a-966e-46ff-b4e7-dae3b2a69fc1	ab64e66d-efc5-47d5-97f3-3a60c962cf36	UNTAR SUAVE	2.45	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	41d71736-8e92-491f-af3f-54d4e5f64af1
aa3c1a9b-d732-43ed-915f-6937602cbb27	ab64e66d-efc5-47d5-97f3-3a60c962cf36	JUESO GOUDA LONCHAS	3.95	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
659b8a61-c04e-4b98-b0c4-ad5bdfe50adc	ab64e66d-efc5-47d5-97f3-3a60c962cf36	GUACAMOLE 500 GR	2.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	70830fd9-d781-426b-8b82-29c5b11772d4
a4051fa3-337f-49fd-b215-27cedba29a6b	ab64e66d-efc5-47d5-97f3-3a60c962cf36	TRONOPIO SURIMI	2.20	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	efaeece6-1aa2-4265-b961-1308cd4aa898
e2df1cdd-ed9a-40a3-9e6d-629843de392c	ab64e66d-efc5-47d5-97f3-3a60c962cf36	NATA MONTAR	1.40	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
0f2476e3-afb6-4d5c-837a-02efdc097b0c	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	GOURMET MAXI	60.00	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	7ecb0a74-daf9-4a17-973d-ee5fb13d91c2
987d2e2c-2888-419e-ac6f-18026e956d67	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	BICARBONATO KILO	0.90	1	2a780a6e-36d7-4754-9d42-461327a485f4	8494dc52-9b7d-4d45-b16e-f8da7905051f
9b4aeb74-86db-4927-9b00-e573df996194	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	VINAGRE LIMPIEZA	2.55	1	2a780a6e-36d7-4754-9d42-461327a485f4	cf6a8fa2-5510-47e9-882f-40d0900cb7c8
ac36fca2-9264-448e-891e-de523be549c8	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	MASCARPONE	1.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
0d36a22f-29f7-4e4f-9d7a-02da2599d8fb	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	UNTAR SUAVE	2.45	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	41d71736-8e92-491f-af3f-54d4e5f64af1
be9b1c42-23d9-485c-9154-07fe8686d375	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	JUESO GOUDA LONCHAS	3.95	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
812a6abd-8a04-4848-94aa-359660c21ba2	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	GUACAMOLE 500 GR	2.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	70830fd9-d781-426b-8b82-29c5b11772d4
40888928-b5fe-410d-a482-0cd4320af35c	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	TRONOPIO SURIMI	2.20	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	efaeece6-1aa2-4265-b961-1308cd4aa898
ee51bdb1-27bb-40c6-bc0c-6cc8b9814e49	84f7ba0e-0302-445c-8cdf-c2004a7b16e9	NATA MONTAR	1.40	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
23ac1511-c212-41de-bb59-7c967c7782a1	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	BICARBONATO KILO	0.90	1	2a780a6e-36d7-4754-9d42-461327a485f4	8494dc52-9b7d-4d45-b16e-f8da7905051f
d1330cef-3cf5-45b1-a625-c1444fd19bcf	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	VINAGRE LIMPIEZA	2.55	1	2a780a6e-36d7-4754-9d42-461327a485f4	cf6a8fa2-5510-47e9-882f-40d0900cb7c8
214be367-c1dc-40c5-ae25-2ba5623c0299	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	MASCARPONE	1.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
5aafcc23-ef91-4f01-809c-80e2e105e768	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	UNTAR SUAVE	2.45	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	41d71736-8e92-491f-af3f-54d4e5f64af1
4fc07ce3-e1fa-4a8d-b228-24ed979b9b38	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	JUESO GOUDA LONCHAS	3.95	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
225b504d-491a-4f34-930a-624997642e2a	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	GUACAMOLE 500 GR	2.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	70830fd9-d781-426b-8b82-29c5b11772d4
07dd7f26-e6f6-4aa6-9a24-a6a205f3a6c5	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	TRONOPIO SURIMI	2.20	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	efaeece6-1aa2-4265-b961-1308cd4aa898
5f07ee5b-f41e-4712-a8b1-73b5d176a2b0	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	NATA MONTAR	1.40	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	b4c1a410-ae10-46ac-bf52-92141ef8b932
2452f421-75c2-41cb-b4ad-d3c58e37bb87	3442b9ff-08eb-46ed-a2ff-ef6472d1899a	GOURMET MAXI	6.50	1	93e2cda2-d9f6-4def-a1e6-e2a857ffe0d7	70830fd9-d781-426b-8b82-29c5b11772d4
\.


--
-- Data for Name: servicios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.servicios (id, nombre, descripcion, activo) FROM stdin;
e459c774-2faf-498a-b3e3-5bf21177d16e	TICKET_PROCESSING_SERVICE	Limits AI processing of documents	t
0bb1bef2-061f-4bbb-86ae-0d59424483cb	MODIFY_TICKET_SERVICE	Limits modification of documents	t
360ac6a4-ac5e-4034-9195-a2f660e5c1a4	CREATE_TICKET_SERVICE	Limits creation of documents	t
\.


--
-- Data for Name: ticket; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ticket (id, nombre_tienda, total, usuario_id, created_at, modified_at) FROM stdin;
15582a11-1d21-410a-87e5-801ea40c66e9	Unknown	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-03-25 06:07:52.725061	2025-03-25 06:07:52.72507
0c199fb2-539e-4fe6-92fd-8e22620c5e68	Unknown	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-03-25 06:09:57.389784	2025-03-25 06:09:57.389798
1c342f02-3073-4993-aa52-d82ac5fae1e0	Unknown	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-03-25 06:11:37.086764	2025-03-25 06:11:37.086785
6524f4a5-29fe-4d23-90fd-786e00ea04c7	Unknown	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-03-25 06:12:41.089454	2025-03-25 06:12:41.089472
2ba40977-c476-4f69-b33e-759d5a4c906e	Unknown	119.91	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-03-26 06:25:23.85674	2025-03-26 06:25:23.856765
f5e4f611-7b2e-4ab6-8334-ce9eed397f6a	Unknown	119.91	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-03-26 06:32:10.685504	2025-03-26 06:32:10.685521
98a128f2-5d36-4fec-bc70-c48776432ad1	Unknown	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-03-29 09:40:49.850672	2025-03-29 09:40:49.850675
5c61adf9-fd19-43f1-b0d1-6a473f003ea5	Unknown	0.00	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-04-02 06:00:56.689956	2025-04-02 06:00:56.689973
4af2d7c2-32a5-4933-b804-a519fbdbbc21	Unknown	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-04-02 06:01:24.707717	2025-04-02 06:01:24.70773
ab64e66d-efc5-47d5-97f3-3a60c962cf36	Unknown	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-04-02 06:06:11.0937	2025-04-02 06:06:11.093703
84f7ba0e-0302-445c-8cdf-c2004a7b16e9	Unknown	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-04-02 06:07:15.896733	2025-04-02 06:07:15.896735
3442b9ff-08eb-46ed-a2ff-ef6472d1899a	Mercadona	20.71	cfbf826a-749f-48a9-a23f-22afd429cedf	2025-04-02 06:10:03.301776	2025-04-08 05:35:04.295043
\.


--
-- Data for Name: uso_servicios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.uso_servicios (id, usuario_id, servicio_id, cuota_id, uso_actual, ultimo_reset) FROM stdin;
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, nombre, apellidos, correo, customer_id, active, passw, subscription_id, last_verified) FROM stdin;
cfbf826a-749f-48a9-a23f-22afd429cedf	David	Florez Mazuera	dflorez02@gmail.com	cus_RrFxvDwPltLoV7	t	$2b$12$0e0AgHxWtI1S.SP3BzrhIOQDbit4r3qg3m9mND9jVDR.XOUI4fWUW	sub_1RB8JKKPUVcoxoHVFpYYzw5t	2025-04-07 05:36:15.403072+00
\.


--
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- Name: cuotas cuotas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cuotas
    ADD CONSTRAINT cuotas_pkey PRIMARY KEY (id);


--
-- Name: items items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_pkey PRIMARY KEY (id);


--
-- Name: servicios servicios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.servicios
    ADD CONSTRAINT servicios_pkey PRIMARY KEY (id);


--
-- Name: ticket tiendas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ticket
    ADD CONSTRAINT tiendas_pkey PRIMARY KEY (id);


--
-- Name: uso_servicios uc_usuario_servicio_cuota; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uso_servicios
    ADD CONSTRAINT uc_usuario_servicio_cuota UNIQUE (usuario_id, servicio_id, cuota_id);


--
-- Name: uso_servicios uso_servicios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uso_servicios
    ADD CONSTRAINT uso_servicios_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_correo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_correo_key UNIQUE (correo);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: idx_categoria_nombre_nivel; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_categoria_nombre_nivel ON public.categorias USING btree (nombre, nivel);


--
-- Name: idx_categoria_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_categoria_parent ON public.categorias USING btree (parent_id);


--
-- Name: idx_cuota_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cuota_id ON public.uso_servicios USING btree (cuota_id);


--
-- Name: idx_item_categoria; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_item_categoria ON public.items USING btree (categoria_id);


--
-- Name: idx_item_subcategoria; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_item_subcategoria ON public.items USING btree (sub_categoria_id);


--
-- Name: idx_servicio_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_servicio_id ON public.cuotas USING btree (servicio_id);


--
-- Name: idx_usuario_servicio; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_usuario_servicio ON public.uso_servicios USING btree (usuario_id, servicio_id);


--
-- Name: categorias categorias_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.categorias(id);


--
-- Name: cuotas cuotas_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cuotas
    ADD CONSTRAINT cuotas_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicios(id) ON DELETE CASCADE;


--
-- Name: items items_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id);


--
-- Name: items items_sub_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_sub_categoria_id_fkey FOREIGN KEY (sub_categoria_id) REFERENCES public.categorias(id);


--
-- Name: items items_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_ticket_id_fkey FOREIGN KEY (receipt_id) REFERENCES public.ticket(id) ON DELETE CASCADE;


--
-- Name: ticket ticket_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ticket
    ADD CONSTRAINT ticket_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: uso_servicios uso_servicios_cuota_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uso_servicios
    ADD CONSTRAINT uso_servicios_cuota_id_fkey FOREIGN KEY (cuota_id) REFERENCES public.cuotas(id) ON DELETE CASCADE;


--
-- Name: uso_servicios uso_servicios_servicio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uso_servicios
    ADD CONSTRAINT uso_servicios_servicio_id_fkey FOREIGN KEY (servicio_id) REFERENCES public.servicios(id) ON DELETE CASCADE;


--
-- Name: uso_servicios uso_servicios_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uso_servicios
    ADD CONSTRAINT uso_servicios_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

