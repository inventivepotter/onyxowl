"""
Comprehensive test data fixtures with 100+ variations per category
"""

# ============================================================================
# EMAIL ADDRESSES - 120 variations
# ============================================================================

EMAIL_TEST_CASES = [
    # Standard formats (30)
    "user@example.com",
    "john.doe@company.co.uk",
    "alice_smith@subdomain.example.org",
    "bob.jones123@test-site.io",
    "mary.wilson@my-company.net",
    "test.user+tag@gmail.com",
    "admin@localhost.localdomain",
    "webmaster@site.museum",
    "info@company.travel",
    "support@help.aero",
    "sales@business.coop",
    "contact@organization.edu",
    "hello@startup.tech",
    "team@project.dev",
    "group@collaborative.agency",
    "person@individual.name",
    "user123@numbers456.biz",
    "a@b.co",
    "x.y.z@long.subdomain.example.com",
    "first.middle.last@company.com",
    "user_name@under_score.com",
    "test-user@dash-domain.org",
    "plus+address@gmail.com",
    "dot.dot.dot@many.dots.here.com",
    "1234567890@numbers.com",
    "email@123.123.123.123",
    "user@domain-one.com",
    "user@domain.name.com",
    "user@domain.co.jp",
    "user@domain.com.au",

    # International domains (20)
    "user@münchen.de",
    "test@中国.cn",
    "email@日本.jp",
    "contact@españa.es",
    "info@москва.ru",
    "admin@québec.ca",
    "user@åland.fi",
    "test@ñoño.mx",
    "email@ümlaut.com",
    "contact@café.fr",
    "user@טעסט.co.il",
    "test@परीक्षा.in",
    "email@δοκιμή.gr",
    "contact@테스트.kr",
    "info@测试.com",
    "admin@тест.ru",
    "user@پست.ir",
    "test@ทดสอบ.th",
    "email@テスト.jp",
    "contact@परिक्षण.in",

    # With numbers and special chars (20)
    "user123@example.com",
    "test456@company.org",
    "email789@website.net",
    "user.name+tag+sorting@example.com",
    "x@example.com",
    "user+mailbox/department=shipping@example.com",
    "!def!xyz%abc@example.com",
    "user%example.com@example.org",
    "_test@example.com",
    "user_@example.com",
    "user-@example.com",
    "user.@example.com",
    "1234567890123456789012345678901234567890123456789012345678901234@example.com",
    "a.b.c.d.e.f.g.h.i.j.k.l.m.n.o.p.q.r.s.t.u.v.w.x.y.z@example.com",
    "user+tag1+tag2+tag3@example.com",
    "my-email-address@my-domain.com",
    "user_name_123@domain-name-456.com",
    "test.email.with.multiple.dots@company.co.uk",
    "first+middle+last@company.org",
    "user=test@example.com",

    # TLDs variations (20)
    "user@domain.com",
    "user@domain.org",
    "user@domain.net",
    "user@domain.edu",
    "user@domain.gov",
    "user@domain.mil",
    "user@domain.int",
    "user@domain.info",
    "user@domain.biz",
    "user@domain.name",
    "user@domain.pro",
    "user@domain.museum",
    "user@domain.coop",
    "user@domain.aero",
    "user@domain.xxx",
    "user@domain.idv",
    "user@domain.tv",
    "user@domain.io",
    "user@domain.me",
    "user@domain.app",

    # Country code TLDs (20)
    "user@domain.us",
    "user@domain.uk",
    "user@domain.ca",
    "user@domain.au",
    "user@domain.de",
    "user@domain.fr",
    "user@domain.jp",
    "user@domain.cn",
    "user@domain.in",
    "user@domain.br",
    "user@domain.mx",
    "user@domain.it",
    "user@domain.es",
    "user@domain.ru",
    "user@domain.kr",
    "user@domain.nl",
    "user@domain.se",
    "user@domain.no",
    "user@domain.dk",
    "user@domain.fi",

    # Edge cases (10)
    "disposable.style.email.with+symbol@example.com",
    "other.email-with-hyphen@example.com",
    "fully-qualified-domain@example.com",
    "user.name+tag+sorting@example.com",
    "x@example.com",
    "example-indeed@strange-example.com",
    "example@s.example",
    "user@tt",
    "test@test.test",
    "very.long.email.address.with.many.dots.and.characters@very.long.domain.name.with.many.levels.example.com",
]

# ============================================================================
# PHONE NUMBERS - 150 variations (multi-country)
# ============================================================================

PHONE_TEST_CASES = [
    # US/Canada formats (25)
    "(555) 123-4567",
    "555-123-4567",
    "555.123.4567",
    "555 123 4567",
    "5551234567",
    "+1 (555) 123-4567",
    "+1-555-123-4567",
    "+1.555.123.4567",
    "+1 555 123 4567",
    "1-555-123-4567",
    "1.555.123.4567",
    "1 555 123 4567",
    "(800) 555-1212",
    "800-555-1212",
    "800.555.1212",
    "+1 (800) 555-1212",
    "(212) 555-0000",
    "(415) 555-9999",
    "(310) 555-8888",
    "(702) 555-7777",
    "1 (555) 123-4567",
    "1(555)123-4567",
    "15551234567",
    "(555)1234567",
    "555 1234567",

    # UK formats (15)
    "020 7123 4567",
    "0207 123 4567",
    "020-7123-4567",
    "020.7123.4567",
    "02071234567",
    "+44 20 7123 4567",
    "+44-20-7123-4567",
    "+44.20.7123.4567",
    "+442071234567",
    "07700 900123",
    "07700-900-123",
    "+44 7700 900123",
    "+447700900123",
    "0141 123 4567",  # Glasgow
    "0161 123 4567",  # Manchester

    # India formats (15)
    "9876543210",
    "8765432109",
    "7654321098",
    "+91 9876543210",
    "+91-9876543210",
    "+91.9876543210",
    "+919876543210",
    "022 1234 5678",  # Mumbai landline
    "011 1234 5678",  # Delhi landline
    "080 1234 5678",  # Bangalore landline
    "+91 22 1234 5678",
    "+91 11 1234 5678",
    "+91 80 1234 5678",
    "0221234567",
    "+912212345678",

    # Australia formats (15)
    "0412 345 678",
    "0412-345-678",
    "0412.345.678",
    "0412345678",
    "+61 412 345 678",
    "+61-412-345-678",
    "+61.412.345.678",
    "+61412345678",
    "02 1234 5678",  # Sydney landline
    "03 1234 5678",  # Melbourne landline
    "07 1234 5678",  # Brisbane landline
    "+61 2 1234 5678",
    "+61 3 1234 5678",
    "+61 7 1234 5678",
    "0755512345",

    # Germany formats (12)
    "030 12345678",
    "030-12345678",
    "030/12345678",
    "03012345678",
    "+49 30 12345678",
    "+49-30-12345678",
    "+49.30.12345678",
    "+493012345678",
    "0171 1234567",  # Mobile
    "+49 171 1234567",
    "040 87654321",  # Hamburg
    "+49 40 87654321",

    # France formats (12)
    "01 23 45 67 89",
    "01-23-45-67-89",
    "01.23.45.67.89",
    "0123456789",
    "+33 1 23 45 67 89",
    "+33-1-23-45-67-89",
    "+33.1.23.45.67.89",
    "+33123456789",
    "06 12 34 56 78",  # Mobile
    "+33 6 12 34 56 78",
    "09 87 65 43 21",
    "+33 9 87 65 43 21",

    # Japan formats (10)
    "03-1234-5678",  # Tokyo
    "03.1234.5678",
    "0312345678",
    "+81 3 1234 5678",
    "+81-3-1234-5678",
    "+8131234567",
    "090-1234-5678",  # Mobile
    "+81 90 1234 5678",
    "+819012345678",
    "06-1234-5678",  # Osaka

    # China formats (10)
    "13812345678",  # Mobile
    "13912345678",
    "15012345678",
    "+86 138 1234 5678",
    "+86-138-1234-5678",
    "+8613812345678",
    "010-12345678",  # Beijing landline
    "021-12345678",  # Shanghai landline
    "+86 10 12345678",
    "+86 21 12345678",

    # Brazil formats (10)
    "(11) 91234-5678",  # São Paulo mobile
    "(21) 98765-4321",  # Rio mobile
    "(11) 1234-5678",   # São Paulo landline
    "+55 11 91234-5678",
    "+55-11-91234-5678",
    "+5511912345678",
    "(85) 3456-7890",   # Fortaleza landline
    "+55 85 3456-7890",
    "11912345678",
    "+5521987654321",

    # Mexico formats (8)
    "(55) 1234-5678",   # Mexico City
    "55-1234-5678",
    "+52 55 1234 5678",
    "+52-55-1234-5678",
    "+525512345678",
    "(81) 8765-4321",   # Monterrey
    "+52 81 8765 4321",
    "5512345678",

    # South Korea formats (8)
    "010-1234-5678",  # Mobile
    "010.1234.5678",
    "01012345678",
    "+82 10 1234 5678",
    "+82-10-1234-5678",
    "+821012345678",
    "02-123-4567",    # Seoul landline
    "+82 2 123 4567",

    # Spain formats (5)
    "+34 612 34 56 78",
    "+34-612-34-56-78",
    "+34612345678",
    "612 34 56 78",
    "91 123 45 67",   # Madrid landline

    # Italy formats (5)
    "+39 338 1234567",
    "+39-338-1234567",
    "+393381234567",
    "338 1234567",
    "06 1234 5678",  # Rome landline
]

# ============================================================================
# CREDIT CARDS - 140 variations
# ============================================================================

CREDIT_CARD_TEST_CASES = [
    # Visa (30 variations - 13 and 16 digit)
    "4111111111111111",
    "4012888888881881",
    "4222222222222",
    "4111-1111-1111-1111",
    "4012-8888-8888-1881",
    "4111 1111 1111 1111",
    "4012 8888 8888 1881",
    "4539578763621486",
    "4556737586899855",
    "4916338506082832",
    "4024007198964305",
    "4485429517622493",
    "4532261615473950",
    "4024007134312079",
    "4916125827020303",
    "4532861682742089",
    "4532635325726206",
    "4024007144242152",
    "4485042691013744",
    "4916524067253727",
    "4024007187488331",
    "4556498960514307",
    "4916341459275618",
    "4024007162544210",
    "4532151970967533",
    "4024 0071 9896 4305",
    "4556-7375-8689-9855",
    "4916 3385 0608 2832",
    "4024.0071.8748.8331",
    "4111.1111.1111.1111",

    # Mastercard (30 variations)
    "5555555555554444",
    "5105105105105100",
    "5555-5555-5555-4444",
    "5105-1051-0510-5100",
    "5555 5555 5555 4444",
    "5105 1051 0510 5100",
    "5425233430109903",
    "5135265076569678",
    "5391369207163619",
    "5476802946486647",
    "5424000000000015",
    "5199822810815169",
    "5252842788120474",
    "5188834325519619",
    "5585822029629441",
    "5293224059984752",
    "5124618417094187",
    "5421825593613663",
    "5190990281925290",
    "5355520017516093",
    "2221000010000015",  # New Mastercard range
    "2223000048400011",
    "2223520043560014",
    "2720994326581252",
    "2720998946581255",
    "2221 0000 1000 0015",
    "2223-0000-4840-0011",
    "5555.5555.5555.4444",
    "5105.1051.0510.5100",
    "2720 9989 4658 1255",

    # American Express (25 variations - 15 digit)
    "378282246310005",
    "371449635398431",
    "378-2822-46310-005",
    "371-4496-35398-431",
    "378 2822 46310 005",
    "371 4496 35398 431",
    "343434343434343",
    "374245455400126",
    "375556917985515",
    "376510699198631",
    "375711740186054",
    "378764018051966",
    "374542438086682",
    "370541116559156",
    "342693811628850",
    "372466898281161",
    "341079096569472",
    "377578682934382",
    "342851537641855",
    "348701960881878",
    "371 4496 35398 431",
    "378 2822 46310 005",
    "343-4343-43434-343",
    "374.2454.55400.126",
    "375 5569 17985 515",

    # Discover (20 variations)
    "6011111111111117",
    "6011000990139424",
    "6011-1111-1111-1117",
    "6011-0009-9013-9424",
    "6011 1111 1111 1117",
    "6011 0009 9013 9424",
    "6011000991300009",
    "6011608198424071",
    "6011111144110011",
    "6011419206305798",
    "6011716907943651",
    "6011589316731650",
    "6011335823169795",
    "6011020047544752",
    "6011414542798914",
    "6011 0009 9130 0009",
    "6011-6081-9842-4071",
    "6011.1111.4411.0011",
    "6011 4192 0630 5798",
    "6011716907943651",

    # JCB (15 variations)
    "3530111333300000",
    "3566002020360505",
    "3530-1113-3330-0000",
    "3566-0020-2036-0505",
    "3530 1113 3330 0000",
    "3566 0020 2036 0505",
    "3528467488345723",
    "3529564196411772",
    "3532837332728562",
    "3538971944231834",
    "3545212045654219",
    "3573438095752071",
    "3530 1113 3330 0000",
    "3566-0020-2036-0505",
    "3528.4674.8834.5723",

    # Diners Club (10 variations - 14 digit)
    "30569309025904",
    "38520000023237",
    "305-6930-9025-904",
    "385-2000-0023-237",
    "305 6930 9025 904",
    "385 2000 0023 237",
    "36148563689286",
    "36110361105971",
    "305.6930.9025.904",
    "361 1036 1105 971",

    # Maestro (10 variations)
    "6762762762762762",
    "5018717934102102",
    "5893229543638340",
    "6304000000000000",
    "6762-7627-6276-2762",
    "5018 7179 3410 2102",
    "6762.7627.6276.2762",
    "5893 2295 4363 8340",
    "6304 0000 0000 0000",
    "6762762762762",  # Variable length
]

# ============================================================================
# SSN and National IDs - 100+ variations
# ============================================================================

SSN_TEST_CASES = [
    # US SSN (30 variations)
    "123-45-6789",
    "987-65-4321",
    "111-22-3333",
    "555-66-7777",
    "999-88-7654",
    "234-56-7890",
    "345-67-8901",
    "456-78-9012",
    "567-89-0123",
    "678-90-1234",
    "789-01-2345",
    "890-12-3456",
    "901-23-4567",
    "012-34-5678",
    "123-45-6780",
    "234-56-7891",
    "345-67-8902",
    "456-78-9013",
    "567-89-0124",
    "678-90-1235",
    "789-01-2346",
    "890-12-3457",
    "901-23-4568",
    "012-34-5679",
    "111-11-1111",
    "222-22-2222",
    "333-33-3333",
    "444-44-4444",
    "555-55-5555",
    "666-66-6666",

    # UK National Insurance (15)
    "AB123456C",
    "CD123456D",
    "EF123456E",
    "GH123456F",
    "IJ123456G",
    "KL123456H",
    "MN123456I",
    "OP123456J",
    "QR123456K",
    "ST123456L",
    "UV123456M",
    "WX123456N",
    "YZ123456A",
    "AB 12 34 56 C",
    "CD 12 34 56 D",

    # Canadian SIN (15)
    "123-456-789",
    "987-654-321",
    "111-222-333",
    "444-555-666",
    "777-888-999",
    "234 567 890",
    "345 678 901",
    "456 789 012",
    "567 890 123",
    "678 901 234",
    "789012345",
    "890123456",
    "901234567",
    "012345678",
    "112233445",

    # Australian TFN (15)
    "123-456-789",
    "987-654-321",
    "111 222 333",
    "444 555 666",
    "777 888 999",
    "234567890",
    "345678901",
    "456789012",
    "567890123",
    "678901234",
    "789 012 345",
    "890 123 456",
    "901 234 567",
    "012 345 678",
    "111222333",

    # Indian Aadhaar (15)
    "1234-5678-9012",
    "9876-5432-1098",
    "1111 2222 3333",
    "4444 5555 6666",
    "7777 8888 9999",
    "2345 6789 0123",
    "3456 7890 1234",
    "4567 8901 2345",
    "5678 9012 3456",
    "6789 0123 4567",
    "123456789012",
    "987654321098",
    "111122223333",
    "444455556666",
    "777788889999",

    # German Tax ID (10)
    "12345678901",
    "98765432109",
    "11111111111",
    "22222222222",
    "33333333333",
    "44444444444",
    "55555555555",
    "66666666666",
    "77777777777",
    "88888888888",
]

# ============================================================================
# Cryptocurrency Addresses - 100+ variations
# ============================================================================

CRYPTO_TEST_CASES = [
    # Bitcoin Legacy (P2PKH) - 30
    "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
    "3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy",
    "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
    "12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S",
    "1dice8EMZmqKvrGE4Qc9bUFf9PX3xaYDp",
    "1FfmbHfnpaZjKFvyi1okTjJJusN455paPH",
    "1KXrWXciRDZUpQwQmuM1DbwsKDLYAYsVLR",
    "16ftSEQ4ctQFDtVZiUBusQUjRrGhM3JYwe",
    "13p1ijLwsnrcuyqcTvJXkq2ASdXqcnEBLE",
    "1Nr8E5xfJy5vG2xcMeWmLzXfEUa5LNyPGu",
    "1QGV3EH7LJ6vYVRPgJGRHdzaZqYSHgZyuM",
    "19DPvPgwQqFqWvmWNarrq8yKXrnRJvLJgF",
    "1LRtF9cN7p2q3xWPqGZRvYWNBRZLbGMtPD",
    "1Fd8RuZqJNG4v56rPD1v6rgYptwnHeJRWs",
    "16VFWjJVVfj6qQgGVuGLGjQnRPe1XnvPM",
    "1LruNZjwamWJXThX2Y8C2d47QqhAkkc5os",
    "1Pa7aQrYKiJE9xwxXJpHJnKkJCBWpgG5k5",
    "17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem",
    "12cgpFdJViXbwHbhrA3TuW1EGnL25Zqc3P",
    "1J6PYEzr4CUoGbnXrELyHszoTSz3wCsCaj",
    "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s",
    "14qViLJfdGaP4EeHnDyJbEGQysnCpwk3gd",
    "1GiRmYx1uCGbxEjPL3hLaFELJkJ5PaRnXg",
    "1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1",
    "1FoWyxwPXuj4C6abqwhjDWdz6D4PZgYRjA",
    "1JGv6wjN1qJzqSJTJnpXPVp9Wk9v5H5Q3G",
    "1KAD5EnzzLtrSo2Da2G4zzD7uZrjk8zRAv",
    "1LdRWTx7A2q6GoBt7rk91khLGvZMRD7Jt3",
    "1MphSvJPGVWPFz2AqGp31JqgYMqJsCv8bx",

    # Bitcoin SegWit (Bech32) - 20
    "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
    "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
    "bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3",
    "bc1q5v5q6qnxdz3rq9c3cklqjqrrw3qmxqv3zvwqpj",
    "bc1qh7vlucjq7gp2t6y8clvnqyzkzzhf6q7pyfz8wl",
    "bc1qnxkd4j2avpcq9dv9q6x3f4qtmkdzcqfk8f7d0p",
    "bc1q07vj3lznsh2g3q8xzqwlm4gfhxzlx6u3fhqmwl",
    "bc1q2v5q6qnxdz3rq9c3cklqjqrrw3qmxqv3zvwqpj",
    "bc1qh7vlucjq7gp2t6y8clvnqyzkzzhf6q7pyfz8wl",
    "bc1qnxkd4j2avpcq9dv9q6x3f4qtmkdzcqfk8f7d0p",
    "bc1q07vj3lznsh2g3q8xzqwlm4gfhxzlx6u3fhqmwl",
    "bc1q5n8ks3jcp2fvpc0yxqr5vwqk0g8q8tj5r3qg8l",
    "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97",
    "bc1q42lja79elem0anu8q8s3h2n687re9jax556pcc",
    "bc1qeklep85ntjz4605drds6aww9u0qr46qzrv5xswd35uhjuj8ahfcqgf6hak",
    "bc1q7cyrfmck2ffu2ud3rn5l5a8yv6f0chkp0zpemf",
    "bc1qwqdg6squsna38e46795at95yu9atm8azzmyvckulcc7kytlcckxswvvzej",
    "bc1q9qzqcuv5qz5yzqzqszqzqv9qqqn9qqqzqzqzqqqqqpz5s7y2",
    "bc1qc7slrfxkknqcq2jevvvkdgvrt8080852dfjewde450xdlk4ugp7szw5tk9",

    # Ethereum - 30
    "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
    "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
    "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
    "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb",
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2",
    "0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826",
    "0x52bc44d5378309EE2abF1539BF71dE1b7d7bE3b5",
    "0x5e575279bf9f4acf0a130c186861454247394c06",
    "0x82A978B3f5962A5b0957d9ee9eEf472EE55B42F1",
    "0x7cB57B5A97eAbe94205C07890BE4c1aD31E486A8",
    "0x9F7dfAb2222A473284205cdDF08a677726d786A0",
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
    "0x4Fabb145d64652a948d72533023f6E7A623C7C53",
    "0x8E870D67F660D95d5be530380D0eC0bd388289E1",
    "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
    "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F",
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "0xBBbbCA6A901c926F240b89EacB641d8Aec7AEafD",
    "0x111111111117dC0aa78b770fA6A738034120C302",
    "0x2b591e99afE9f32eAA6214f7B7629768c40Eeb39",
    "0x0D8775F648430679A709E98d2b0Cb6250d2887EF",

    # Litecoin - 20
    "LM2WMpR1Rp6j3Sa59cMXMs1SPzj9eXpGc1",
    "LQ4i7FLNzYMnJDWr4WDvWjp3rqVSDt3MgK",
    "LUWPbpM43E2p7ZSh8cyTBEkvpHmr3cB8Ez",
    "LePmFngKfK3VDN8i2DKA1Mg3VgaYXUBzaH",
    "LhK2kQwiaAvhjWY799cZvMyYwnQAcxkarH",
    "LTDqGhv3eabDLq3dHkLEGSJhAPNPp5pJ3T",
    "LUcfaAPZuwUqMsMLUWgY4L8wjC4tXNDGq3",
    "LZW3YSHYLQevJWQw7nXcqcmdPLWyUudQ2U",
    "LhGrNQhCrKz7BhfWBV2R3y31j9NYaLkdLn",
    "LPGwJ3d7X9R6LvJUAcv6vS6LAp4vWTfFnN",
    "MVY7jHKBBjAV7UXCnKqWs4yTCH7xJwWujE",
    "MN1E9qvFXiJiGQJUEwJv3B3NNMwxZVBfYG",
    "MT2vpkL1jvmH5D7qXUqcCbP9xvAGNgFxWW",
    "MP8S7B9XZb8U5nKkjQAK2FHFPQnKKtXXZD",
    "MW6pLJYLpFEFwVnMMTSDdSF2KzYZkJfGsE",
    "LfF6p8xWqvQXjKwJ5iNJ8V9Lp1YvqvZdKx",
    "LTdsVS8VDw2uqgP8wJwq9pEvkHPJAaRXrE",
    "LYa8JqMzpCiqy6V7M6HzMH3XfUJPj7yfqU",
    "LM3JK9eJtYLT3HsC6CAqAu6C8ZDLdA2zYq",
    "LRpZ3FJ5gFZ4DgUNxfW6cRRQuE3xtXZQNz",
]

# ============================================================================
# Helper Function
# ============================================================================

def get_all_test_data():
    """
    Get all test data organized by category

    Returns:
        Dictionary with category names as keys and test cases as values
    """
    return {
        "emails": EMAIL_TEST_CASES,
        "phones": PHONE_TEST_CASES,
        "credit_cards": CREDIT_CARD_TEST_CASES,
        "ssn": SSN_TEST_CASES,
        "crypto": CRYPTO_TEST_CASES,
    }

def get_test_count():
    """Get count of test cases per category"""
    return {
        "emails": len(EMAIL_TEST_CASES),
        "phones": len(PHONE_TEST_CASES),
        "credit_cards": len(CREDIT_CARD_TEST_CASES),
        "ssn": len(SSN_TEST_CASES),
        "crypto": len(CRYPTO_TEST_CASES),
        "total": (
            len(EMAIL_TEST_CASES) +
            len(PHONE_TEST_CASES) +
            len(CREDIT_CARD_TEST_CASES) +
            len(SSN_TEST_CASES) +
            len(CRYPTO_TEST_CASES)
        )
    }
