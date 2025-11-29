--
-- Derechos Reservados (C) 2025, Octavio Alvarez Piza <octalgh@alvarezp.org>
-- Copyright (C) 2025, Octavio Alvarez Piza. All rights reserved.
--
-- This program is free software: you can redistribute it and/or
-- modify it under the terms of the GNU Affero General Public
-- License as published by the Free Software Foundation, either
-- version 3 of the License.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
-- Affero General Public License for more details.
--
-- You should have received a copy of the GNU Affero General Public
-- License version 3 along with this program. If not, see
-- <https://www.gnu.org/licenses/>.
--


--
-- PostgreSQL database dump
--

\restrict lfVTUQN0NRh5XHPHbPwfbYdhSrvyyjTfPhkJZ9ati9ktrZhXjOCNSh2rT0Zmivc

-- Dumped from database version 17.6 (Debian 17.6-0+deb13u1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-0+deb13u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: get_direct_children(cidr, cidr[]); Type: FUNCTION; Schema: public; Owner: alvarezp
--

CREATE FUNCTION public.get_direct_children(parent cidr, candidates cidr[]) RETURNS SETOF cidr
    LANGUAGE plpgsql
    AS $$
DECLARE
    r          cidr;
    last_child cidr := NULL;
BEGIN
    -- Iterate only over descendents of parent
    FOR r IN
        SELECT x
        FROM   unnest(candidates) AS x
        WHERE  x << parent          -- discard non-descendents
        ORDER  BY x                 -- sort by (network id, masklen)
    LOOP
        IF last_child IS NULL THEN
            last_child := r;
            RETURN NEXT r;

        ELSIF r << last_child THEN
            -- grandchild or further, discard
            CONTINUE;

        ELSE
            -- doesn't fit into last_child: we have a new last_child
            last_child := r;
            RETURN NEXT r;
        END IF;
    END LOOP;

    RETURN;
END;
$$;


ALTER FUNCTION public.get_direct_children(parent cidr, candidates cidr[]) OWNER TO alvarezp;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: fixed_prefixes; Type: TABLE; Schema: public; Owner: alvarezp
--

CREATE TABLE public.fixed_prefixes (
    prefix cidr NOT NULL,
    description character varying
);


ALTER TABLE public.fixed_prefixes OWNER TO alvarezp;

--
-- Name: observed_prefixes; Type: TABLE; Schema: public; Owner: alvarezp
--

CREATE TABLE public.observed_prefixes (
    prefix cidr,
    poll_method character varying,
    device character varying,
    entry_type character varying,
    description character varying
);


ALTER TABLE public.observed_prefixes OWNER TO alvarezp;

--
-- Name: all_prefixes; Type: VIEW; Schema: public; Owner: alvarezp
--

CREATE VIEW public.all_prefixes AS
 SELECT 'OBSERVED'::text AS record_type,
    observed_prefixes.prefix,
    observed_prefixes.poll_method AS method,
    observed_prefixes.device,
    observed_prefixes.entry_type,
    observed_prefixes.description
   FROM public.observed_prefixes
UNION ALL
 SELECT 'FIXED'::text AS record_type,
    fixed_prefixes.prefix,
    NULL::character varying AS method,
    NULL::character varying AS device,
    NULL::character varying AS entry_type,
    fixed_prefixes.description
   FROM public.fixed_prefixes;


ALTER VIEW public.all_prefixes OWNER TO alvarezp;

--
-- Name: all_prefixes_with_best_description; Type: VIEW; Schema: public; Owner: alvarezp
--

CREATE VIEW public.all_prefixes_with_best_description AS
 WITH with_weight AS (
         SELECT all_prefixes.record_type,
            all_prefixes.prefix,
            all_prefixes.method,
            all_prefixes.device,
            all_prefixes.entry_type,
            all_prefixes.description,
                CASE
                    WHEN (all_prefixes.record_type = 'FIXED'::text) THEN 1000
                    WHEN ((all_prefixes.entry_type)::text ~~ 'interface %'::text) THEN 600
                    WHEN ((all_prefixes.entry_type)::text = 'route'::text) THEN 300
                    WHEN ((all_prefixes.entry_type)::text = 'specification'::text) THEN 100
                    ELSE 1
                END AS weight
           FROM public.all_prefixes
        ), best_weight AS (
         SELECT with_weight.prefix,
            max(with_weight.weight) AS weight
           FROM with_weight
          GROUP BY with_weight.prefix
        )
 SELECT w.record_type,
    bw.prefix,
    max((w.description)::text) AS description,
    (count(w.description))::text AS description_count
   FROM (best_weight bw
     LEFT JOIN with_weight w ON ((((bw.prefix)::inet = (w.prefix)::inet) AND (bw.weight = w.weight))))
  GROUP BY w.record_type, bw.prefix;


ALTER VIEW public.all_prefixes_with_best_description OWNER TO alvarezp;

--
-- Data for Name: fixed_prefixes; Type: TABLE DATA; Schema: public; Owner: alvarezp
--

COPY public.fixed_prefixes (prefix, description) FROM stdin;
\.


--
-- Data for Name: observed_prefixes; Type: TABLE DATA; Schema: public; Owner: alvarezp
--

COPY public.observed_prefixes (prefix, poll_method, device, entry_type, description) FROM stdin;
0.0.0.0/0	\N	\N	specification	IPv4 space
127.0.0.0/8	\N	\N	specification	Loopback space
169.254.0.0/16	\N	\N	specification	Link local block
224.0.0.0/4	\N	\N	specification	Multicast space
10.0.0.0/8	\N	\N	specification	Private address space
172.16.0.0/12	\N	\N	specification	Private address space
192.168.0.0/16	\N	\N	specification	Private address space
192.0.2.0/24	\N	\N	specification	Documentation: TEST-NET-1
198.51.100.0/24	\N	\N	specification	Documentation: TEST-NET-2
203.0.113.0/24	\N	\N	specification	Documentation: TEST-NET-3
198.18.0.0/15	\N	\N	specification	Benchmark space
::/0	\N	\N	specification	IPv6 space
::1/128	\N	\N	specification	Loopback address
::ffff:0.0.0.0/96	\N	\N	specification	IPv4-mapped
64:ff9b::/96	\N	\N	specification	NAT64 IPv4/IPv6 translation
64:ff9b:1::/48	\N	\N	specification	Local-use IPv4/IPv6 translation
100::/64	\N	\N	specification	Discard prefix
2001::/32	\N	\N	specification	Teredo tunneling
2001:20::/28	\N	\N	specification	ORCHIDv2
2001:db8::/32	\N	\N	specification	Documentation
2002::/16	\N	\N	specification	6to4
3fff::/20	\N	\N	specification	Documentation
5f00::/16	\N	\N	specification	IPv6 Segment Routing
fc00::/7	\N	\N	specification	Unique-Local addresses
fe80::/64	\N	\N	specification	Link-local addresses
fe80::/10	\N	\N	specification	Link-local addresses (reserved block)
ff00::/8	\N	\N	specification	Multicast
\.


--
-- Name: fixed_prefixes fixed_segments_pkey; Type: CONSTRAINT; Schema: public; Owner: alvarezp
--

ALTER TABLE ONLY public.fixed_prefixes
    ADD CONSTRAINT fixed_segments_pkey PRIMARY KEY (prefix);


--
-- Name: fixed_prefixes_prefix_idx; Type: INDEX; Schema: public; Owner: alvarezp
--

CREATE INDEX fixed_prefixes_prefix_idx ON public.fixed_prefixes USING btree (prefix);


--
-- Name: observed_prefixes_prefix_idx; Type: INDEX; Schema: public; Owner: alvarezp
--

CREATE INDEX observed_prefixes_prefix_idx ON public.observed_prefixes USING btree (prefix);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: TABLE fixed_prefixes; Type: ACL; Schema: public; Owner: alvarezp
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.fixed_prefixes TO "www-data";


--
-- Name: TABLE observed_prefixes; Type: ACL; Schema: public; Owner: alvarezp
--

GRANT SELECT ON TABLE public.observed_prefixes TO "www-data";


--
-- Name: TABLE all_prefixes; Type: ACL; Schema: public; Owner: alvarezp
--

GRANT SELECT ON TABLE public.all_prefixes TO "www-data";


--
-- Name: TABLE all_prefixes_with_best_description; Type: ACL; Schema: public; Owner: alvarezp
--

GRANT SELECT ON TABLE public.all_prefixes_with_best_description TO "www-data";


--
-- PostgreSQL database dump complete
--

\unrestrict lfVTUQN0NRh5XHPHbPwfbYdhSrvyyjTfPhkJZ9ati9ktrZhXjOCNSh2rT0Zmivc

