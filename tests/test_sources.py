from hatari.data.sources import COLUMNS, load_french_synthetic, load_mendeley, load_uci


def test_uci_keeps_quotes_and_maps_labels(tmp_path):
    (tmp_path / "uci_sms_spam").mkdir()
    (tmp_path / "uci_sms_spam" / "SMSSpamCollection").write_text(
        'ham\tOk "lar" see you\nspam\tWIN £100 now, call 0800\n', encoding="utf-8")

    frame = load_uci(tmp_path)

    assert list(frame.columns) == COLUMNS
    assert frame["text"].tolist() == ['Ok "lar" see you', "WIN £100 now, call 0800"]
    assert frame["suspicious"].tolist() == [False, True]
    assert frame["row"].tolist() == [1, 2]


def test_mendeley_lowercases_labels_and_strips_tabs(tmp_path):
    (tmp_path / "mendeley_smishing").mkdir()
    (tmp_path / "mendeley_smishing" / "Dataset_5971.csv").write_text(
        "LABEL,TEXT,URL,EMAIL,PHONE\nham,hello,No,No,No\nSmishing,\tVerify your account,Yes,No,No\n"
        "Spam,Cheap offer,No,No,No\n", encoding="utf-8")

    frame = load_mendeley(tmp_path)

    assert frame["original_label"].tolist() == ["ham", "smishing", "spam"]
    assert frame["text"].tolist()[1] == "Verify your account"
    assert frame["suspicious"].tolist() == [False, True, True]
    assert frame["row"].tolist() == [2, 3, 4]


def test_french_synthetic_keeps_split_and_template_group(tmp_path):
    (tmp_path / "french_synthetic.csv").write_text(
        "id,text,label,domain,spam_category,split,template_group\n"
        "a,Bonjour,legitimate,sms,unknown,train,g1\n"
        "b,Envoyez 2000 FCFA,spam,email,scam,test,g2\n", encoding="utf-8")

    frame = load_french_synthetic(tmp_path)

    assert frame["origin"].unique().tolist() == ["synthetic"]
    assert frame["channel"].tolist() == ["sms", "email"]
    assert frame["suspicious"].tolist() == [False, True]
    assert frame["published_split"].tolist() == ["train", "test"]
    assert frame["template_group"].tolist() == ["g1", "g2"]
